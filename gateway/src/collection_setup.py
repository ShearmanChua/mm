import json
import os
import pandas as pd
from tqdm import tqdm

from utils.ESManager import DocManager
from utils.WeaviateManager import VectorManager
from doc_utils.preprocess import M2E2_Preprocessor
from doc_utils.wikipedia import Wikipedia
from viz_utils.faceid import get_face_emb
from viz_utils.image_inference import Inference

FACE_COLLECTION_NAME = "face_db"
DOC_COLLECTION_NAME = "documents_m2e2"
DATA_ROOT = '../data'

if __name__ == '__main__':
    DocMgr = DocManager()
    VecMgr = VectorManager()

    # M2E2 Schema
    with open(os.path.join(DATA_ROOT, 'm2e2_files/m2e2_map.json')) as f:
        m2e2_map = json.load(f)
    m2e2_map = m2e2_map['documents_m2e2']['mappings']

    # Wikipedia Schema
    with open(os.path.join(DATA_ROOT, 'wikipedia_files/wiki_map.json')) as f:
        wiki_map = json.load(f)
    wiki_map = wiki_map['wikipedia']['mappings']
    
    # Face Uploading Setup
    facedb_schema = {'doc_id': 'str'}
    ref_face_path = os.path.join(DATA_ROOT, 'reference_faces')

    DocMgr.create_collection('wikipedia', schema=wiki_map, custom_schema=True)
    DocMgr.create_collection(DOC_COLLECTION_NAME, schema=m2e2_map, custom_schema=True)
    VecMgr.create_collection(FACE_COLLECTION_NAME, schema=facedb_schema)

    # Populate Wikipedia into ES
    # wiki_emb = os.path.join(DATA_ROOT, 'wikipedia_files/all_entities_large.t7')
    # wiki_ent = os.path.join(DATA_ROOT, 'wikipedia_files/entity.jsonl')
    # wiki = Wikipedia(wiki_emb, wiki_ent)
    # for collated_docs in wiki.ingest():
    #     DocMgr.create_document('wikipedia', collated_docs, id_field='id')

    # Populate Reference Faces into Weaviate
    for id in tqdm(os.listdir(ref_face_path)):
        face_emb = get_face_emb(ref_face_path, id)
        if face_emb['response']=='200':
            facedb_doc = {
                "doc_id": id,
                "vector": face_emb['emb']
            }
            VecMgr.create_document(FACE_COLLECTION_NAME, documents=facedb_doc)
        else:
            print(f"Failed to create {id}, no faces found")
    
    # Populate M2E2 Dataset into ES & Upload Images to Image Server
    preproc = M2E2_Preprocessor()
    m2e2_csv = os.path.join(DATA_ROOT, 'm2e2_files/m2e2.csv')
    m2e2_titles = os.path.join(DATA_ROOT, 'm2e2_files/titles.json')
    all_docs = preproc(m2e2_csv, m2e2_titles)
    r = DocMgr.create_document(DOC_COLLECTION_NAME, all_docs)
    print(r['response'])


    # Visual Inferences
    viz_inference = Inference(FACE_COLLECTION_NAME)
    img_folder = '/images/M2E2/'
    for id, inferences in viz_inference.run_inference(img_folder):
        es_res = DocMgr.query_collection(DOC_COLLECTION_NAME, {"ID":id})
        if es_res['response']=='No documents found.':
            print(f"id {id} not found in ES.")
            continue # Some articles have images but no textual body, so their documents were not ingested in ES
        es_id = es_res['api_resp'][0]['_id']
        print(id)
        DocMgr.update_document(DOC_COLLECTION_NAME, es_id, {
            'visual_entities': inferences
        })
