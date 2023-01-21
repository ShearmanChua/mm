import base64
import json
import requests
import os
from tqdm import tqdm

from viz_utils.faceid import single_inference
from utils.WeaviateManager import VectorManager

class Inference():
    def __init__(self) -> None:
        self.vecdb = VectorManager()

    def run_inference(self, folder):
        for i, subfolder in enumerate(tqdm(os.listdir(folder))):
            inference_list = []
            for img_file in os.listdir(os.path.join(folder,subfolder)):
                file_index = img_file.split('.')[0]
                file_key = f'/images/M2E2/{subfolder}/{file_index}.h5'            

                r_fn = single_inference(os.path.join(folder, subfolder, img_file))
                res_fn = r_fn['body']

                res_fn['box'] = [[max(b, 0) for b in a]
                    for a in res_fn['box']]  # Clip negative value to 0