import json
import os

from utils.ESManager import DocManager
from utils.WeaviateManager import VectorManager
from viz_utils.img_server import ImageUploader
from viz_utils.faceid import get_face_emb

if __name__ == '__main__':
    DocMgr = DocManager()
    VecMgr = VectorManager()

    # M2E2 Schema
    with open('../data/m2e2_map.json') as f:
        m2e2_map = json.load(f)
    m2e2_map = m2e2_map['documents_m2e2']['mappings']

    # Wikipedia Schema
    with open('../data/wiki_map.json') as f:
        wiki_map = json.load(f)
    wiki_map = wiki_map['wikipedia']['mappings']
    
    # Face Uploading Setup
    facedb_schema = {'doc_id': 'str'}
    ref_face_path = '../data/reference_faces'

    DocMgr.create_collection('wikipedia', schema=wiki_map, custom_schema=True)
    DocMgr.create_collection('documents_m2e2', schema=m2e2_map, custom_schema=True)
    VecMgr.create_collection('face_db', schema=facedb_schema)

    # Upload M2E2 source images
    imu = ImageUploader()
    imu.upload_all('../data/images_m2e2')

    # Populate face ref db
    for id in os.listdir(ref_face_path):
        face_emb = get_face_emb(ref_face_path, id)
        if face_emb['response']=='200':
            facedb_doc = {
                "doc_id": id,
                "vector": face_emb['emb']
            }
            VecMgr.create_document('face_db', documents=facedb_doc)
        else:
            print(f"Failed to create {id}, no faces found")
    