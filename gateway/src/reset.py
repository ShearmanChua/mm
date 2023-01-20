from utils.ESManager import DocManager
from utils.WeaviateManager import VectorManager


if __name__ == '__main__':
    DocMgr = DocManager()
    VecMgr = VectorManager()

    DocMgr.delete_collection('wikipedia')
    DocMgr.delete_collection('documents_m2e2')
    VecMgr.delete_collection('face_db')