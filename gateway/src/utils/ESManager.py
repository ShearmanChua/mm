import os

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, scan, streaming_bulk

# Map common python types to ES Types
TYPE_MAP =  {
    "int":"integer",
    "float":"float",
    "double":"double",
    "str": "text",
    "bool": "boolean",
    "datetime": "date",
    "list[int]":"integer",
    "list[str]":"text",
    "list[float]": "float",
    "list[double]": "double",
    "torch.tensor": "dense_vector",
    "numpy.ndarray": "dense_vector"
}

class DocMgr():
    def __init__(self):
        self.url = f"https://{os.environ.get('ELASTICSEARCH_HOST')}:{os.environ.get('ELASTICSEARCH_C_PORT')}"
        self.username = os.environ.get('ELASTIC_USERNAME')
        self.password = os.environ.get('ELASTIC_PASSWORD')
        self.client = Elasticsearch(self.url, 
                                    verify_certs=False, 
                                    basic_auth=(self.username, self.password))

        
    def _check_valid_values(self, map_dict:dict) -> int:
        """
        Traverse mapping dictionary to ensure that all types are valid types within TYPE_MAP

        Args:
            map_dict (dict): Mapping to be checked

        Returns:
            int: 0 if there is invalid types, 1 otherwise

        """
        ret_val = 1
        for k, v in map_dict.items():
            if isinstance(v, dict):
                ret_val = self._check_valid_values(v)
            else:
                if not v in TYPE_MAP:
                    print(f"'{v}' type for '{k}' NOT FOUND")
                    return 0

        return ret_val * 1
    
    def _traverse_map (self, map_dict:dict) -> int:
        """
        Traverse mapping dictionary to convert data type into framework specific type

        Args:
            map_dict (dict): Mapping to be used to create ES index

        Returns:
            dict: updated mapping dictionary

        """
        dictionary ={"properties":dict()}
        for k, v in map_dict.items():
            if isinstance(v, dict):
                dictionary['properties'][k]= self._traverse_map(v)
            else:
                dictionary['properties'][k]={"type":TYPE_MAP[v]}       
        return dictionary
    
    def create_collection(self, collection_name: str, schema: dict) -> dict:
        """
        Create the index on ElasticSearch

        Args:
            collection_name (str): Index name of ES
            schema (dict): Mapping to be used to create ES index

        Returns:
            dict: response of error, or 200 if no errors caught
            
        """
        try:
            assert type(schema)==dict
        except Exception as e:
            return {"response":f"{e.__class__.__name__}: Type of 'schema' is not dict"}
        try:
            assert type(collection_name)==str
        except Exception as e:
            return {"response":f"{e.__class__.__name__}: Type of 'collection_name' is not str"}

        mapping_validity = self._check_valid_values(schema)
        if not mapping_validity:
            return {"response": "KeyError: data type not found in TYPE_MAP"}
        updated_mapping = self._traverse_map(schema)
        try:
            self.client.indices.create(index=collection_name, mappings=updated_mapping)
        except Exception as e:
            return {"response":f"{e}"}
        return {"response":"200"}
    
    def delete_collection(self, collection_name: str) -> dict:
        """
        Create the index on ElasticSearch

        Args:
            collection_name (str): Index name of ES
            schema (dict): Mapping to be used to create ES index

        Returns:
            dict: response of error, or 200 if no errors caught

        """
        try:
            self.client.indices.delete(index=collection_name)
        except Exception as e:
            return {"response": f"{e}"}
        return {"response":"200"}