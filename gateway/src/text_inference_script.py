import requests
import json
from typing import List, Dict
import pandas as pd
import ast
import re
import time

from haystack.document_stores import ElasticsearchDocumentStore

def ner_inference(ner_dict):

    response = requests.post('http://ner-api:8080/bulk_inference', json={'data': ner_dict})
    ner_results = response["inference"]

    return ner_results

def relation_inference(re_dict):

    response = requests.post('http://re-api:8088/bulk_inference', json={'data': ner_dict})
    ner_results = response["inference"]

    return ner_results

def generate_entity_linking_df(results_df):

    entities_linking_df = pd.DataFrame(
        columns=['doc_id', 'mention', 'context_left', 'context_right'])
        

if __name__ == '__main__':

    start = time.time()

    document_store = ElasticsearchDocumentStore(host="elasticsearch",
                                                port="9200",
                                                username="elastic",
                                                password="changeme",
                                                scheme="https",
                                                verify_certs=False,
                                                index='formula1_articles', # index to get documents from
                                                search_fields=['content', 'title'])

    documents = document_store.get_all_documents()

    articles_df = pd.DataFrame(
        columns=['ID', 'text', 'elasticsearch_ID'])

    for document in documents:
        articles_df.loc[-1] = [document.meta['ID'], document.content, document.id]  # adding a row
        articles_df.index = articles_df.index + 1  # shifting index
        articles_df = articles_df.sort_index()  # sorting by index

    print(articles_df.info())
    print(articles_df.head())

    ner_inference_df = articles_df[['text']]
    ner_dict = ner_inference_df.to_dict('records')
    ner_results = ner_inference(ner_dict)
    ner_results_df = pd.DataFrame.from_records(ner_results, columns=['text','predictions'])

    ner_results_df = pd.merge(articles_df, ner_results_df, on=['text'])

    print(ner_results_df.info())
    print(ner_results_df.head())

    ner_results_df = ner_results_df.rename(columns={"predictions": "predicted_ner"})

    re_inference_df = ner_results_df[['text','predicted_ner']]
    re_dict = re_inference_df.to_dict('records')
    re_results = relation_inference(re_dict)
    re_results_df = pd.DataFrame.from_records(re_results, columns=['text','predictions'])
    re_results_df = re_results_df.rename(columns={"predictions": "predicted_relations"})

    relations_ner_results_df = pd.merge(ner_results_df, re_results_df, on=['text'])
