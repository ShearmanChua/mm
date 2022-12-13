import yaml
import weaviate
import torch

def read_yaml(file_path='config.yaml'):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

config = read_yaml()
URL = config['database']['URL']

class VectorManager:
    def __init__(self) -> None:
        """
        Set up the connection

        INPUT: None
        ------------------------------------

        RETURNS: None
        ------------------------------------
        """
        self._client = weaviate.Client('http://weaviate:8080/')

    def delete_collection(self, collection_name: str) -> None:
        self._client.schema.delete_class(collection_name)

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
            print(key, val)
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
            print("Collection successfilly created")
        except Exception as e:
            if '422' in str(e):
                print("Collection has been created")
            else:
                print(f"Unknwon error with error message -> {e}")


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
        where_filter = {
            'operator': 'Equal',
            'valueText': properties.get('id_no'),
            'path': ['id_no']
        }

        response = self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
        if len(response['data']['Get'][collection_name]) > 1:
            print("There exist duplicated files")
            return
        elif len(response['data']['Get'][collection_name]) == 1:
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
        where_filter = {
            'operator': 'Equal',
            'valueText': id_no,
            'path': ['id_no']
        }
        return self._client.query.get(collection_name, ["id_no", "_additional {vector}"]).with_where(where_filter).do()

    def _id2uuid(self, collection_name, id):
        where_filter = {
            'operator': 'Equal',
            'valueText': id,
            'path': ["id_no"]
        }

        query_result =  self._client.query.get(collection_name, ["id_no", "_additional {id}"]).with_where(where_filter).do()
        uuid = query_result['data']['Get'][collection_name][0]['_additional']['id']
        return uuid

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
        # if not document['properties'].get('id_no'):
        #     print('Lack of id_no result in ambiguous document to update')
        #     return
        # self._client.data_object.update(
        #     data_object = {}, 
        #     class_name = collection_name, 
        #     uuid = uuid, 
        #     vector = new_vector
        # )



