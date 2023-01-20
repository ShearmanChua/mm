import ast
import json
import pandas as pd
from tqdm import tqdm
from viz_utils.img_server import ImageUploader

class M2E2_Preprocessor:
    def __init__(self):
        self.uploader = ImageUploader()
    def __call__(self, file_path, title_file):
        with open(title_file) as f:
            title_map = json.load(f)
        doc_df = pd.read_csv(file_path)
        doc_df['images'] = doc_df['images'].apply(lambda images: ast.literal_eval(images))
        doc_df['image_captions'] = doc_df['image_captions'].apply(
            lambda image_captions: ast.literal_eval(image_captions))
        
        docs = []
        for idx, row in tqdm(doc_df.iterrows(), total=len(doc_df)):
            server_paths = []   
            for image_filename in row['images']:
                server_path = self.uploader.upload_single_image(image_filename)
                server_paths.append(server_path)
            doc = {}
            doc = {
                "content": row['text'],
                "ID": row['doc_ID'],
                "title": title_map[str(row['doc_ID'])],
                "link": row['url'],
                "images": server_paths,
                "image_captions": row['image_captions'],
                "timestamp": row['timestamp']
            }

            docs.append(doc)
        return docs