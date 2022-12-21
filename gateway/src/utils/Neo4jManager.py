import collections
import os
from typing import Optional, List, Dict, Union

import yaml
import json
import re
import ast
import pandas as pd
from tqdm import tqdm

from datetime import datetime
import pytz
from neo4j import GraphDatabase
from neo4j.time import DateTime

# Map common python types to neo4j Types
TYPE_MAP =  {
    "int":"Integer",
    "float":"Float",
    "str": "String",
    "bool": "Boolean",
    "datetime": "DateTime",
    "list[int]":"List",
    "list[str]":"List",
    "list[float]": "List",
    "list[double]": "List",
    "dict": "Map",
}

class Neo4jConnection:

    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                self.__uri, auth=(self.__user, self.__pwd))
            self.bookmark = self.driver.session().last_bookmark()
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def query(self, query, parameters=None, db=None):
        assert self.driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.driver.session(
                database=db) if db is not None else self.driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            return {"response":f"{e}"}
        finally:
            if session is not None:
                session.close()
        return response

class Neo4jManager():
    def __init__(self):
        self.url = os.environ.get('NEO4J_URL')
        self.username = os.environ.get('NEO4J_USERNAME')
        self.password = os.environ.get('NEO4J_PASSWORD')
        self.neo4j_conn = Neo4jConnection(uri=self.url,
                                          user=self.username,
                                          pwd=self.password)

        
    def create_collection(self, collection_name: str):
        pass

    def delete_collection(self,collection_name: str):
        pass

    def create_index(self, node_index_name: str, node_label: str, node_id: str, db=None):
        with self.neo4j_conn.driver.session(database=db) if db is not None else self.neo4j_conn.driver.session() as session:
            return session.run("CREATE INDEX {} IF NOT EXISTS FOR (n:{}) ON (n.{})".format(node_index_name, node_label, node_id))

    def merge_node(self, node_labels, node_attributes, db=None):
        with self.neo4j_conn.driver.session(database=db) if db is not None else self.neo4j_conn.driver.session() as session:
            node_labels = ":".join(node_labels)
            node_attributes = "{"+", ".join([re.sub('[^A-Za-z0-9]+', '_', k)+" : '"+str(node_attributes[k]).replace(
                "'", "").encode("ascii", "ignore").decode()+"'" for k in node_attributes.keys() if not k[0].isdigit()])+"}"
            # print("MERGE (p:{} {}) RETURN p".format(node_label, node_attributes))'
            print("MERGE (p:{} {}) RETURN p".format(node_labels, node_attributes))
            print("\n")
            return session.run("MERGE (p:{} {}) RETURN p".format(node_labels, node_attributes)).single().value()

    def create_node(self, collection_name: str, nodes: List[dict]):
        for node in tqdm(nodes):
            node_attributes = node.copy()
            for key,node_attribute in node_attributes:
                if type(node_attribute) == datetime:
                    neo4j_datetime = DateTime(node_attribute.year, node_attribute.month, node_attribute.day, node_attribute.minute, node_attribute.second)
                    node_attributes.update({key, neo4j_datetime})
            node_labels = node['node_labels']
            node_id = node['node_id']
            self.merge_node(node_labels,node)
            for label in node_labels:
                self.create_index(label.capitalize(), label, node_id)

    def _generate_edges(self, entities_triples_df, relations_dict, db=None):
        for idx, triple in tqdm(entities_triples_df.iterrows(), total=len(entities_triples_df)):
            source_node_label = "Entity"
            source_node_attributes = {
                "entity": triple.subject, "doc_id": str(triple.doc_id)}
            target_node_label = "Entity"
            target_node_attributes = {
                "entity": triple.object, "doc_id": str(triple.doc_id)}
            relation_type = triple.relation.replace(" ", "_")
            relation_type = re.sub('[^A-Za-z0-9]+', '_', relation_type)
            edge_attributes = {"relation_id": str(
                relations_dict[triple.relation]), "doc_id": str(triple.doc_id), "timestamp": str(triple.timestamp)}
            merge_edge(source_node_label, source_node_attributes, target_node_label,
                    target_node_attributes, relation_type, edge_attributes, db)

    def create_graph(self, collection_name: str, triples: List[dict]):
        triples_df = pd.json_normalize(triples, max_level=0)
        self.create_node(triples_df['Subject'].values.tolist())
        self.create_node(triples_df['Object'].values.tolist())

        return
    
  
    