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

def entity_linking_inference(dataset):

    response = requests.post('http://0.0.0.0:5050/bulk_inference', json=dataset)

    df = pd.json_normalize(response.json(), max_level=0)

    print(df)
    print(df.info())

    # df.to_csv("data/articles_entity_linked.csv", index=False)

    return df

def generate_entity_linking_df(results_df):

    entities_linking_df = pd.DataFrame(
        columns=['doc_id', 'mention', 'mention_span', 'context_left', 'context_right'])
    
    for idx, row in results_df.iterrows():
        doc_id = row['ID']
        document_text = row['text']
        if type(row['predicted_ner']) == str:
            ner_mentions = ast.literal_eval(row['predicted_ner'])
        else:
            ner_mentions = row['predicted_ner']
        for entity in ner_mentions:
            mention = document_text[entity[0]:entity[1]]
            mention_span = tuple(entity[0], entity[1])
            left_context = document_text[entity[0]-100:entity[0]]
            right_context = document_text[entity[1]:entity[1]+100]
            entities_linking_df.loc[-1] = [doc_id, mention, mention_span,
                                           left_context, right_context]  # adding a row
            entities_linking_df.index = entities_linking_df.index + 1  # shifting index
            entities_linking_df = entities_linking_df.sort_index()  # sorting by index
    
    return entities_linking_df

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

    entity_linking_df = generate_entity_linking_df(relations_ner_results_df)

    entity_linking_json = entity_linking_df.to_json(orient="records")
    entity_linking_json = json.loads(entity_linking_json)
    entity_linking_results = entity_linking_inference(entity_linking_json)

    list_of_cluster_dfs = entity_linking_results.groupby('doc_id')

    entities = []
    ids = []
    for group, cluster_df in list_of_cluster_dfs:
        doc_entities = []
        doc_id = cluster_df['doc_id'].tolist()[0]
        mentions = cluster_df['mention'].tolist()
        mention_spans = cluster_df['mention_span'].tolist()
        entity_links = cluster_df['entity_link'].tolist()
        entity_names = cluster_df['entity_names'].tolist()

        for idx, mention in enumerate(mentions):
            mention = dict()
            mention['mention'] = mention
            mention['mention_span'] = mention_spans[idx]
            mention['entity_link'] = entity_links[idx]
            mention['entity_name'] = entity_names[idx]
            doc_entities.append(mention)
        ids.append(doc_id)
        entities.append(doc_entities)

    entities_df = pd.DataFrame()
    entities_df['ID'] = ids
    entities_df['identified_entities'] = entities

    results_df = pd.merge(relations_ner_results_df, entities_df, on=["ID"])

    print(results_df.info())
    results_df.to_csv("data/text_inference.csv", index=False)

    # Update results to ElasicSearch
    for idx, row in results_df.iterrows():
        meta_dict = {'entities_identified': row['identified_entities'], 'relations_identified': row['predicted_relations']}
        document_store.update_document_meta(
            id=row['elasticsearch_ID'], meta=meta_dict)

    end = time.time()
    print("Time to complete entity and relation extraction and entity linking", end - start)
