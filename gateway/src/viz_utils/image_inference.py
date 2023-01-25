import base64
import json
import requests
import os
from tqdm import tqdm

from viz_utils.faceid import face_inference_b64
from viz_utils.objdet import obj_inference_b64
from viz_utils.img_server import ImageUploader
from utils.WeaviateManager import VectorManager

class Inference():
    def __init__(self, face_collection) -> None:
        self.face_collection = face_collection
        self.vecdb = VectorManager()
        self.img_mgr = ImageUploader()

    def run_inference(self, folder):
        for i, subfolder in enumerate(tqdm(self.img_mgr.listdir(folder))):
            inference_list = []
            doc_id = int(subfolder.split('.')[-1])
            for img_file in self.img_mgr.listdir(os.path.join(folder,subfolder)):
                detection_dict = {}
                file_index = img_file.split('.')[0]
                file_key = os.path.join(folder, subfolder, f'{file_index}.h5')
                detection_dict['file_name'] = file_key
                img_bytes = self.img_mgr.download_single_image(file_key)

                # face inference
                r_fn = face_inference_b64(img_bytes)
                res_fn = r_fn['body']
                res_fn['box'] = [[max(int(b), 0) for b in a]
                    for a in res_fn['box']]  # Clip negative value to 0
                id_list = []
                probs_list = []
                for emb in res_fn['emb']:
                    vec_result = self.vecdb.get_top_k(self.face_collection, emb)
                    emb_id = vec_result['response'][0]['response']['properties']['doc_id']
                    emb_prob = vec_result['response'][0]['certainty']
                    id_list.append(emb_id)
                    probs_list.append(emb_prob)
                mask = [True if a > 0.8 else False for a in probs_list]
                id_list = [str(a) if mask[id_list.index(a)]
                       else "-1" for a in id_list]
                detection_dict['person_bbox'] = res_fn['box']
                detection_dict['person_id'] = id_list
                detection_dict['person_conf'] = probs_list

                # obj inference
                res_yolo = obj_inference_b64(img_bytes)
                mask = [True if a > 0.5 else False for a in res_yolo['conf']]
                obj_list = [a if mask[res_yolo['classes'].index(
                    a)] else 'Unknown' for a in res_yolo['classes']]
                res_yolo['bbox'] = [[max(b, 0) for b in a]
                                    for a in res_yolo['bbox']]
                detection_dict['obj_bbox'] = res_yolo['bbox']
                detection_dict['obj_class'] = obj_list
                detection_dict['obj_conf'] = res_yolo['conf']

                inference_list.append(detection_dict)
            print(doc_id)
            yield doc_id, inference_list