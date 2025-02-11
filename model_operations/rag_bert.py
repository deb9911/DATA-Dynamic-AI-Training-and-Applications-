from sentence_transformers import SentenceTransformer
from faiss import IndexFlatIP
import numpy as np


class RAGFeatureClass():
    def __init__(self):
        pass

    def model_selection(self):
        # Load a sentence embedding model (e.g., Sentence-BERT)
        model = SentenceTransformer('all-mpnet-base-v2')

        # Sample knowledge base (replace with your actual data)
        knowledge_base = [
            "The capital of France is Paris.",
            "The Eiffel Tower is located in Paris.",
            "The Earth revolves around the Sun."
        ]

        # Create embeddings for the knowledge base
        knowledge_embeddings = model.encode(knowledge_base)

        # Create a Faiss index
        index = IndexFlatIP(knowledge_embeddings.shape[1])
        index.add(knowledge_embeddings)

        # Get embedding for a query
        query_embedding = model.encode(["What is the capital of France?"])[0]

        # Find nearest neighbors in the knowledge base
        distances, indices = index.search(query_embedding.reshape(1, -1), k=2)
        relevant_documents = [knowledge_base[i] for i in indices[0]]

        print(relevant_documents)


if __name__ == '__main__':
    rag_feature_obj = RAGFeatureClass()
    rag_feature_obj.model_selection()

