import base64
import requests
import os

class ImageUploader:
    def __init__(self):
        self.server_address = 'image_server'
        self.source_root = '../data/images_m2e2'

    def upload_single_image(self, filename):

        # full_name = os.path.join(self.source_root,filename+'.jpg')
        full_name = os.path.join(self.source_root, filename)

        with open(full_name, "rb") as f:
            im_bytes = f.read()
        im_b64 = base64.b64encode(im_bytes).decode("utf8")

        body = {
            'filename': filename.strip('.jpg'),
            'image': im_b64
        }
        r = requests.put(
            f'http://{self.server_address}:8000/upload/', json=body)

        return r.json()['server_path']

    def upload_all(self, data_root=None):
        if data_root != None:
            self.source_root = data_root
        all_server_path = []
        for i in os.listdir(self.source_root):
            server_path = self.upload_single_image(i)
            all_server_path.append(server_path)
        return all_server_path

    def download_single_image(self, filename):
        body = {
            'server_path':filename
        }
        r = requests.get(
            f'http://{self.server_address}:8000/download/', json=body)
        if r.json()['status']=='success':
            return r.json()['image']
        else:
            return ''

    def listdir(self, path):
        body = {
            'folder_path':path
        }
        r = requests.get(
            f'http://{self.server_address}:8000/listdir/', json=body)
        return r.json()['files']