import os
import base64
import json
import requests

FACEID_ENDPT = f"http://{os.environ.get('FACENET_HOST')}:{os.environ.get('FACENET_C_PORT')}"

def get_face_emb(folder_root, id):
    face_list = []
    headers = {'Content-type': 'application/json',
    'Accept': 'text/plain'}
    for faces in os.listdir(os.path.join(folder_root, id)):
        with open(os.path.join(folder_root, id, faces), "rb") as f:
            im_bytes = f.read()
        im_b64 = base64.b64encode(im_bytes).decode("utf8")
        face_list.append({"image":im_b64})
    payload = json.dumps({"images":face_list})

    r_fn = requests.post(
        f"{FACEID_ENDPT}/embedding", data=payload, headers=headers)
    res_fn = json.loads(r_fn.text)
    return res_fn

def face_inference_b64(im_bytes):
    headers = {'Content-type': 'application/json',
            'Accept': 'text/plain'}
    payload = json.dumps({"image":im_bytes})
    r_fn = requests.post(
        f"{FACEID_ENDPT}/detect", data=payload, headers=headers)
    res_fn = json.loads(r_fn.text)
    return res_fn

def face_inference(filename):
    with open(filename, "rb") as f:
        im_bytes = f.read()
    im_b64 = base64.b64encode(im_bytes).decode("utf8")
    res_fn = face_inference_b64(im_b64)
    return res_fn


