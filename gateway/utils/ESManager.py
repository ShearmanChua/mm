import os

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, scan, streaming_bulk

class DocMgr():
    def __init__(self):
        self.url = f"https://{os.environ.get('ELASTICSEARCH_HOST')}:{os.environ.get('ELASTICSEARCH_C_PORT')}"
        self.username = os.environ.get('ELASTIC_USERNAME')
        self.password = os.environ.get('ELASTIC_PASSWORD')
        self.client = Elasticsearch(self.url, 
                                    verify_certs=False, 
                                    basic_auth=(self.username, self.password))