import ast
import json
import numpy as np
import pandas as pd
import torch

from tqdm import tqdm

MAX_BULK_SIZE=10000

class Wikipedia:
    def __init__(self, emb_file, entity_file):
        self.embs_path = emb_file
        self.entity_path = entity_file
    def ingest(self):
        wikipedia_embeddings = torch.load(self.embs_path)
        print("Number of wikipeda data embeddings: ", wikipedia_embeddings.shape[0])

        json_list = []
        with open(self.entity_path, "r") as fin:
            lines = fin.readlines()
            for line in lines:
                entity = json.loads(line)
                json_list.append(entity)
        print('Number of wikipedia pages: ', len(json_list))


        docs = []
        for index in tqdm(range(0, len(json_list))):
            doc = {}
            uid = json_list[index]['idx'].split("curid=")[-1]

            doc = {
                'content': json_list[index]['text'],
                'idx':json_list[index]['idx'], 
                'title':json_list[index]['title'],
                'entity':json_list[index]['entity'],
                'id': uid,
                'embedding':wikipedia_embeddings[index].detach().cpu().tolist()
            }


            docs.append(doc)

            if len(docs) == MAX_BULK_SIZE:
                yield docs
                docs = []
        if len(docs)!=0:       
            yield docs