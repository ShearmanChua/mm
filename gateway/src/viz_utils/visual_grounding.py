import json
import os
import requests

from viz_utils.img_server import ImageUploader

VG_ENDPT = f"http://{os.environ.get('VG_HOST')}:{os.environ.get('VG_C_PORT')}"

class VisualGrounding():
    """
    Takes in a whole document and resolves all unknown entities
    """
    def __init__(self) -> None:
        self.img_mgr = ImageUploader()
        self.header = {'Content-type': 'application/json',
                        'Accept': 'text/plain'}

    def set_img_caption(self, image_path, caption):
        img_bytes = self.img_mgr.download_single_image(image_path)
        if img_bytes == '':
            print("Image not found!!")
            return {}
        payload = json.dumps({"image":img_bytes, "caption": caption})
        r = requests.post(VG_ENDPT, data=payload, headers=self.headers)
        return r.json()

