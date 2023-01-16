from utils.ESManager import DocManager
from utils.WeaviateManager import VectorManager

if __name__ == '__main__':
    DocMgr = DocManager()
    VecMgr = VectorManager()

    es_mapping = {}
    weaviate_schema = {'id_no': 'str'}

    DocMgr.create_collection('documents_m2e2', schema=es_mapping, custom_schema=True)
    VecMgr.create_collection('face_db', schema=weaviate_schema)

    # Populate face db 