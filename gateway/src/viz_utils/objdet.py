import os
import base64
import json
import requests

OBJDET_ENDPT = f"http://{os.environ.get('OBJDET_HOST')}:{os.environ.get('OBJDET_C_PORT')}"

def obj_inference_b64(im_bytes):
    headers = {'Content-type': 'application/json',
                'Accept': 'text/plain'}
    payload = json.dumps({"image":im_bytes})
    r_yolo = requests.post(
        f"{OBJDET_ENDPT}/infer", data=payload, headers=headers)
    res_yolo = json.loads(r_yolo.text)
    return res_yolo

def obj_inference(filename):
    with open(filename, "rb") as f:
        im_bytes = f.read()
    im_b64 = base64.b64encode(im_bytes).decode("utf8")
    res_yolo = obj_inference_b64(im_b64)
    return res_yolo

