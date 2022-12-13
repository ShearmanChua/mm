import weaviate
import torch
import os
import copy

class VectorManager:
    def __init__(self) -> None:
        """
        Set up the connection

        INPUT: None
        ------------------------------------

        RETURNS: None
        ------------------------------------
        """
        self._client = weaviate.Client(f"http://{os.environ.get('WEAVIATE_HOST')}:{os.environ.get('WEAVIATE_C_PORT')}")
        
    def _id2uuid(self, collection_name: str, id_no: str) -> str:
        where_filter = {
            'operator': 'Equal',
            'valueText': id_no,
            'path': ["id_no"]
        }

        query_result =  self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
        uuid = query_result['data']['Get'][collection_name][0]['_additional']['id']
        return uuid
    
    def _exists(self, id_no:str) -> bool:
        where_filter = {
            'operator': 'Equal',
            'valueText': id_no,
            'path': ['id_no']
        }
        response = self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
        if len(response['data']['Get'][collection_name]) > 1:
            print("There exist duplicated files")
            return True
        elif len(response['data']['Get'][collection_name]) == 1:
            return True
        return False

    def delete_collection(self, collection_name: str) -> None:
        try:
            self._client.schema.delete_class(collection_name)
            print('Successfully deleted')
        except Exception as e:
            if '400' in str(e):
                print('Collection does not exist so nothing to delete')
            else:
                print(f"Unknown error with error message -> {e}")
            
    def delete_document(self, collection_name: str, id_no: str) -> None:
        # Check if the id exist
        id_exists = self._exists(id_no)
        
        if not id_exists:
            print("This id does not exist so no deletion is done")
            return
        
        uuid = self._id2uuid(collection_name, id_no)
        
        try:
            self._client.data_object.delete(uuid=uuid, class_name=collection_name)
            print('Successfully deleted')
        except Exception as e:
            print(f"Unknown error with error message -> {e}")

    def create_collection(self, collection_name: str, schema: dict) -> None:
        """
        create a collection of documents

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        schema:             Schema for each document
                            example: {
                                "properties":{
                                    "id_no": ["text"],
                            }}

        RETURNS: None
        ------------------------------------
        """
        # Ensure that there is a id_no for the schema
        if not schema['properties'].get('id_no'):
            print('Lack of id_no as an attribute in property')
            return
        
        # Extract the document information into a list
        properties = []
        for key, val in schema['properties'].items():
            properties.append({'name': key, 'dataType': val})

        # Proper formetting for creating the schema
        document_schema = {
            'class': collection_name,
            'vectorizer': 'none',
            'properties': properties
        }

        # Try to create schema. If exists, gracefully exit.
        try:
            self._client.schema.create_class(document_schema)
            print("Collection Successfully created")
        except Exception as e:
            if '422' in str(e):
                print("Collection has been created")
            else:
                print(f"Unknown error with error message -> {e}")


    def create_document(self, collection_name: str, properties: dict, embedding: torch.Tensor) -> None:
        """
        create a document in a specified collecton

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

        RETURNS: None
        ------------------------------------
        """
        # Check if the id_no attribute exist
        if not properties.get('id_no'):
            print('Lack of id_no as an attribute in property')
            return

        # Check if the id exist
        id_exists = self._exists(id_no)
        
        if id_exists:
            print("This id already existed please use update instead")
            return

        # Create document
        self._client.data_object.create(
          properties,
          collection_name,
          vector = embedding
        )

    def read_document(self, collection_name: str, id_no: str) -> dict:
        """
        Find a document in a specified collecton

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        id_no:              id of document
                            example: "72671"

        RETURNS: None
        ------------------------------------
        """
        # Create filter and search
        uuid = self._id2uuid(collection_name, id_no)
        return self._client.data_object.get_by_id(uuid = uuid, class_name = collection_name, with_vector = True)

    

    def update_document(self, collection_name: str, document: dict) -> None:
        """
        Update a document in a specified collecton

        INPUT: 
        ------------------------------------
        collection_name:    Name of collection
                            example shape:  'Faces'
        document:           dctionary format of the update document
                            {
                                'id_no': '4848272',
                                'vector': torch.Tensor([[
                                    1, 2, ..., 512
                                ]]),
                                'name': 'Trump'
                            }

        RETURNS: None
        ------------------------------------
        """
        if not document.get('id_no'):
            print('Lack of id_no result in ambiguous document to update')
            return
        if not self._exists(document['id_no']):
            print('Attempt to update a non-existent document. No update is done')
            return
        uuid = self._id2uuid(collection_name, document['id_no'])
        temp = copy.deepcopy(document)
        if 'vector' in document.keys():
            new_vector = temp['vector']
            if len(document.keys()) == 2:
                self._client.data_object.update(
                    data_object = {}, 
                    class_name = collection_name, 
                    uuid = uuid, 
                    vector = new_vector
                )
            else:
                del temp['id_no']
                del temp['vector']
                try:
                    self._client.data_object.update(
                        data_object = temp, 
                        class_name = collection_name, 
                        uuid = uuid, 
                        vector = new_vector
                    )
                except Exception as e:
                    if '400' in str(e):
                        print("Unknown field(s) in document")
                    else:
                        print(f"Unknown error with error message -> {e}")
                    