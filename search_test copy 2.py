# Install necessary libraries
# !pip install --upgrade paddlenlp faiss-cpu

import faiss
import numpy as np
import paddle
from transformers import BertTokenizer, BertModel
import logging

# Load the tokenizer and model
MODEL_NAME = "ethanyt/guwenbert-base"
tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
model = BertModel.from_pretrained(MODEL_NAME)
model.eval()

def generate_embedding(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
        add_special_tokens=True,
    )
    with paddle.no_grad():
        outputs = model(**inputs)
        # outputs is a tuple: (sequence_output, pooled_output)
        sequence_output, pooled_output = outputs
        embedding = pooled_output  # Use the pooled output
    return embedding.numpy()

# Sample data
documents = [
    {"id": 0, "text": "菩萨发愿度众生，愿以无量功德普度众生，成就无上正等正觉。", "metadata": {"chapter": 1, "volume": 5}},
    {"id": 1, "text": "如来成佛无量功德，广度众生，普利有情，成就无上正等正觉。", "metadata": {"chapter": 2, "volume": 5}},
    {"id": 2, "text": "众生皆有佛性，佛性本自清净，众生因无明烦恼而迷失本性。", "metadata": {"chapter": 3, "volume": 6}},
    {"id": 3, "text": "四谛法门，苦集灭道，苦谛是指人生的痛苦，集谛是指痛苦的原因，灭谛是指痛苦的消灭，道谛是指消灭痛苦的方法。", "metadata": {"chapter": 4, "volume": 7}},
    {"id": 4, "text": "量子力学是研究微观粒子运动规律的科学，揭示了微观世界的奇妙现象。", "metadata": {"chapter": 5, "volume": 8}},
    {"id": 5, "text": "相对论是爱因斯坦提出的理论，揭示了时空的本质，改变了人类对宇宙的认识。", "metadata": {"chapter": 6, "volume": 9}},
    {"id": 6, "text": "人工智能是计算机科学的一个分支，研究如何让计算机模拟人类智能，解决复杂问题。", "metadata": {"chapter": 7, "volume": 10}},
    {"id": 7, "text": "深度学习是人工智能的一个重要领域，通过模拟人脑的神经网络结构，解决复杂的模式识别问题。", "metadata": {"chapter": 8, "volume": 11}},
]

# Generate embeddings for the documents
embeddings = []
metadata_store = {}
for doc in documents:
    print(f"Generating embedding for document: {doc['text']}")
    emb = generate_embedding(doc["text"])
    embeddings.append(emb)
    metadata_store[doc["id"]] = doc["metadata"]

# Normalize embeddings
embeddings_np = np.vstack(embeddings)
embeddings_np = embeddings_np / np.linalg.norm(embeddings_np, axis=1, keepdims=True)

# Build FAISS index using Inner Product
d = embeddings_np.shape[1]
index = faiss.IndexFlatIP(d)
index.add(embeddings_np)

# Function to search for similar documents using FAISS
def search_faiss(query_text, top_k=3):
    query_embedding = generate_embedding(query_text)
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    D, I = index.search(np.array([query_embedding]), top_k)
    results = []
    for i, idx in enumerate(I[0]):
        results.append({
            "text": documents[idx]["text"],
            "metadata": metadata_store[idx],
            "similarity": D[0][i]
        })
    return results

# Test the system with different queries
test_queries = [
    "微观粒子",
]

# Run tests
for query in test_queries:
    print(f"Query: {query}")
    results = search_faiss(query)
    for result in results:
        print(f"Text: {result['text']}, Similarity: {result['similarity']:.4f}, Metadata: {result['metadata']}")
    print("-" * 50)
