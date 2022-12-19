import weaviate
import torch
import os
import copy
from typing import Union, List
import numpy

class VectorManager:
    TYPE_MAP = {
        "int":["int"],
        "float":["number"],
        "double":["number"],
        "str": ["text"],
        "bool": ["boolean"],
        "datetime": ["date"],
        "list[int]":["int[]"],
        "list[str]":["text[]"],
        "list[float]": ["number[]"],
        "list[double]": ["number[]"],
        "torch.tensor": "",
        "numpy.ndarray": ""
    }
    
    def __init__(self) -> None:
        """
        Set up the connection

        INPUT: None
        ------------------------------------

        RETURNS: None
        ------------------------------------
        """
        self._client = weaviate.Client(f"http://{os.environ.get('WEAVIATE_HOST')}:{os.environ.get('WEAVIATE_C_PORT')}")
        
    def _traverse_map(self, schema:dict) -> List:
        """
        Restructure the schema

        INPUT: 
        ------------------------------------
        schema:             Schema for each document
                            example: {
                                "id_no": "str",
                            }

        RETURNS: 
        ------------------------------------
        List:               List of dictionary for the field mapping
                            example: [{
                                "name" : "id_no",
                                "dataType" : ["text"],
                                }]
        """
        temp = []
        for k, v in schema.items():
            try:
                self.TYPE_MAP.get(v)
                if v != "":
                    temp.append({
                        "name": k,
                        "dataType": self.TYPE_MAP[v]
                    })
            except:
                return []
        return temp
        
    def _id2uuid(self, collection_name: str, id_no: str) -> dict:
        """
        Convert id_no to uuid

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        id_no:              id of document
                            example: '72671'

        RETURNS: 
        ------------------------------------
        Dict:               Dictionary with the uuid or errors
                            example: {
                                'uuid': '1fbf7a0f-1904-4c21-afd8-6bda380e51fd'
                            }
        """
        if self._exists(collection_name, id_no):
            where_filter = {
                'operator': 'Equal',
                'valueText': id_no,
                'path': ["id_no"]
            }
            query_result =  self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
            uuid = query_result['data']['Get'][collection_name][0]['_additional']['id']
            return {'uuid': uuid}
        return {'errors': f'id: {id_no} is not found'}
    
    def _exists(self, collection_name: str, id_no: str) -> bool:
        """
        Convert id_no to uuid

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        id_no:              id of document
                            example: "72671"

        RETURNS: 
        ------------------------------------
        bool:               If the id_no exists in the collection
                            example: True or False
        """
        where_filter = {
            'operator': 'Equal',
            'valueText': id_no,
            'path': ['id_no']
        }
        response = self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
        if 'data' in response and len(response['data']['Get'][collection_name]) == 1:
            return True
        return False

    def delete_collection(self, collection_name: str) -> dict:
        """
        Delete the entire collection

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example:  'Faces'

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        try:
            self._client.schema.delete_class(collection_name)
        except Exception as e:
            return {'response':f"{e}"}
        return {'response': "200"}
            
    def delete_document(self, collection_name: str, id_no: str) -> dict:
        """
        Delete a document in a weaviate class

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        id_no:              id of document
                            example: "72671"

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        uuid = self._id2uuid(collection_name, id_no)
        if 'uuid' in uuid:
            try:
                self._client.data_object.delete(uuid = uuid['uuid'], class_name=collection_name)
                return {'response': "200"}
            except Exception as e:
                return {'response': f"Unknown error with error message -> {e}"}
        return {'response': uuid['errors']}


    def create_collection(self, collection_name: str, schema: dict) -> dict:
        """
        Create a collection of documents

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        schema:             Schema for each document
                            example: {
                                "id_no": ["text"],
                            }

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        if not schema.get('id_no'):
            return {'response': 'Lack of id_no as an attribute in property'}
        properties = self._traverse_map(schema)
        if properties == []:
            return {'response': 'Unknown data type in the field'}
        document_schema = {
            'class': collection_name,
            'vectorizer': 'none',
            'properties': properties
        }
        try:
            self._client.schema.create_class(document_schema)
        except Exception as e:
            return {'response': f"Unknown error with error message -> {e}"}
        return {'response': "200"}

    def create_document(self, collection_name: str, properties: dict, embedding: torch.Tensor) -> dict:
        """
        Create a document in a specified collection

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        properties:         Schema for the document
                            example: {
                                "id_no": 72671
                            }
        embedding:          embedding for the document
                            example: torch.Tensor([[
                                1, 2, ..., 512
                            ]])

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        # Check if the id_no attribute exist
        if not properties.get('id_no'):
            return {'response': 'Lack of id_no as an attribute in property'}
        # Check if the id exist
        id_exists = self._exists(collection_name, properties['id_no'])
        if id_exists:
            return {'response': 'This id already existed, please use update instead'}
        # Create document
        try:
            self._client.data_object.create(
              properties,
              collection_name,
              vector = embedding
            )
            return {'response': "200"}
        except Exception as e:
            if "vector lengths don't match"in str(e):
                self.delete_document(collection_name, properties['id_no'])
                return {'response':"Mismatch vector length, creation failed"}
            else:
                return {'response': f"{e}"}

    def read_document(self, collection_name: str, id_no: str) -> dict:
        """
        Return a matching document in a specified collection

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        id_no:              id of document
                            example: "72671"

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        if not self._exists(collection_name, id_no):
            return {'response': 'Attempt to read a non-existent document. No reading is done'}
        # Create filter and search
        uuid = self._id2uuid(collection_name, id_no)
        if 'uuid' in uuid:
            return {'response': self._client.data_object.get_by_id(uuid = uuid['uuid'], class_name = collection_name, with_vector = True)}
        return {'response': uuid['errors']}
    
    def get_top_k(self, collection_name: str, target_embedding: Union[list, numpy.ndarray, torch.Tensor], top_k: int = 1) -> dict:
        """
        Return the dictionary with the response key holding the list of near documents

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        target_embedding:   Query embedding to find document with high cosine similarity
                            example: torch.Tensor([0.5766745, 0.9341823, 0.7021697, 0.54776406, 0.013553977])
        top_k:              integer value for the number of documents to return. Default is 1
                            example: 3

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with list or errors
                            example: {
                                response: [{
                                    'class': 'Faces',
                                    'creationTimeUnix': 1671076617122,
                                    'id': '9d62d87b-bb17-4736-8714-e1455ffa2b01',
                                    'lastUpdateTimeUnix': 1671076617122,
                                    'properties': {'id_no': '11', 'new': '2'},
                                    'vector': [0.5766745, 0.9341823, 0.7021697, 0.54776406, 0.013553977],
                                    'vectorWeights': None,
                                    'certainty': 0.9999999403953552
                                }]
                            }
                            
        """
        if top_k < 1:
            return {'response': 'Invalid top_k'}
        query_vector = {'vector': target_embedding}
        res = self._client.query.get(collection_name, ["id_no", "_additional {certainty, id}"]).with_near_vector(query_vector).do()
        if 'errors' in res:
            return {'response': res['errors']}
        try:
            limit = min(top_k, len(res['data']['Get'][collection_name]))
            top_id = res['data']['Get'][collection_name][:limit]
            top_results = [ self.read_document(collection_name, document['id_no']) for document in top_id]
            for document, res in zip(top_id, top_results):
                res['certainty'] = document['_additional']['certainty']
            return {'response': top_results}
        except Exception as e:
            return {'response': f'{e}'}

    def update_document(self, collection_name: str, document: dict) -> dict:
        """
        Update a document in a specified collection

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        document:           dictionary format of the updated document
                            {
                                'id_no': '4848272',
                                'vector': torch.Tensor([[
                                    1, 2, ..., 512
                                ]]),
                                'name': 'Trump'
                            }

        RETURNS: 
        ------------------------------------
        dict:               Dictionary with the success code 200 or errors
                            example: {'response': "200"}
        """
        if not document.get('id_no'):
            return {'response': 'Lack of id_no result in an ambiguous document to update'}
        if len(document.keys()) == 1:
            return {'response': f'Only {document.keys()} is found which insufficient to update'}
        uuid = self._id2uuid(collection_name, document['id_no'])
        if 'uuid' in uuid:
            temp = copy.deepcopy(document)
            if 'vector' in document.keys():
                new_vector = temp['vector']
                del temp['id_no']
                del temp['vector']
                previous_vector = self._client.data_object.get_by_id(uuid = uuid['uuid'], class_name = collection_name, with_vector = True)['vector']
                try:
                    self._client.data_object.update(
                        data_object = temp, 
                        class_name = collection_name, 
                        uuid = uuid['uuid'],
                        vector = new_vector
                    )
                    return {'response': "200"}
                except Exception as e:
                    if "vector lengths don't match"in str(e):
                        document['vector'] = previous_vector
                        self.update_document(collection_name, document)
                        return {'response': "Mismatch vector length, updating failed"}
                    else:
                        return {'response': f'{e}'}
            else:
                del temp['id_no']
                try:
                    self._client.data_object.update(
                        data_object = temp, 
                        class_name = collection_name, 
                        uuid = uuid['uuid'],
                    )
                    return {'response': "200"}
                except Exception as e:
                    return {'response': f'{e}'}
        return {'response': uuid['errors']}
                    