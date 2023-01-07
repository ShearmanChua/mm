import base64
import json
import os
import requests
from tqdm import tqdm


from utils.ESManager import DocManager

"""
Images that belong in the same article should be placed in the subfolder.
The subfolder should be the article id. 

Pre-requisite:
Elasticsearch index 
"""

IMAGE_FOLDER = ""
FACENET_ENDPT = ""
YOLO_ENDPT = ""
INDEX_NAME = 'documents_m2e2'

if __name__ == '__main__':
    for i, subfolder in enumerate(tqdm(os.listdir(IMAGE_FOLDER))):
        inference_list = []
        print(subfolder)
        for img_file in os.listdir(IMAGE_FOLDER+'/'+subfolder):
            print(img_file)
            detection_dict = {}
            file_index = img_file.split('.')[0]
            file_key = '/images/M2E2/{}/{}.h5'.format(subfolder, file_index)
            with open(IMAGE_FOLDER+'/'+subfolder+'/'+img_file, "rb") as f:
                im_bytes = f.read()
            im_b64 = base64.b64encode(im_bytes).decode("utf8")

            headers = {'Content-type': 'application/json',
                       'Accept': 'text/plain'}
            payload = json.dumps({"image": im_b64})

            r_fn = requests.post(
                f"{FACENET_ENDPT}/infer", data=payload, headers=headers)
            res_fn = json.loads(r_fn.text)

            r_yolo = requests.post(
                f"{YOLO_ENDPT}/infer", data=payload, headers=headers)
            res_yolo = json.loads(r_yolo.text)

            detection_dict['file_name'] = file_key

            # Facenet Inference
            mask = [True if a > 0.65 else False for a in res_fn['cos_conf']]
            id_list = [str(a) if mask[res_fn['cos_id'].index(a)]
                       else "-1" for a in res_fn['cos_id']]
            res_fn['bb'] = [[max(b, 0) for b in a]
                            for a in res_fn['bb']]  # Clip negative value to 0
            detection_dict['person_bbox'] = res_fn['bb']
            detection_dict['person_id'] = id_list
            detection_dict['person_conf'] = res_fn['cos_conf']
            for index, face in enumerate(res_fn['emb']):
                payload = json.dumps(
                    {"face": face, "file_name": file_key, "index": index})
                r_fs = requests.put(
                    f"{config['endpt']['face_server']}/upload", data=payload, headers=headers)
            # YOLO Inference
            mask = [True if a > 0.5 else False for a in res_yolo['conf']]
            obj_list = [a if mask[res_yolo['classes'].index(
                a)] else 'Unknown' for a in res_yolo['classes']]
            res_yolo['bbox'] = [[max(b, 0) for b in a]
                                for a in res_yolo['bbox']]
            detection_dict['obj_bbox'] = res_yolo['bbox']
            detection_dict['obj_class'] = obj_list
            detection_dict['obj_conf'] = res_yolo['conf']

            inference_list.append(detection_dict)

        q = {
            "script": {
                "source": "ctx._source.visual_entities=params.infer",
                "params": {
                    "infer": inference_list
                },
                "lang": "painless"
            },
            "query": {
                "match": {
                    "ID": subfolder.split('.')[-1]
                }
            }
        }
        client.update_by_query(
            body=q, index=INDEX_NAME)
