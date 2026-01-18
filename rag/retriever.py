from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

def build_retriever(index):
    retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
    return RetrieverQueryEngine(retriever=retriever)
