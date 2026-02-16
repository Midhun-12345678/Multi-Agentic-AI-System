from llama_index.core import VectorStoreIndex

def build_index(documents):
    return VectorStoreIndex.from_documents(documents)
