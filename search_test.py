# Install necessary libraries
# !pip install --upgrade paddlepaddle paddlenlp sentencepiece faiss-cpu

import faiss
import numpy as np
import paddle
from paddlenlp.transformers import *
from paddlenlp.utils.env import PPNLP_HOME
import logging
import os
import shutil

logging.basicConfig(level=logging.DEBUG)

# Define a constant for the model name
MODEL_NAME = "ernie-3.0-medium-zh"

# Clear the model cache
tokenizer_dir = os.path.join(PPNLP_HOME, 'models', MODEL_NAME)
model_dir = os.path.join(PPNLP_HOME, 'models', MODEL_NAME)

if os.path.exists(tokenizer_dir):
    shutil.rmtree(tokenizer_dir)
    print(f"Deleted tokenizer directory: {tokenizer_dir}")
else:
    print(f"Tokenizer directory does not exist: {tokenizer_dir}")

if os.path.exists(model_dir):
    shutil.rmtree(model_dir)
    print(f"Deleted model directory: {model_dir}")
else:
    print(f"Model directory does not exist: {model_dir}")

# Load the tokenizer and model with force_download=True
tokenizer = ErnieTokenizer.from_pretrained(MODEL_NAME)
model = ErnieModel.from_pretrained(MODEL_NAME)

# Test the tokenizer
text = '菩萨发愿度众生'
tokens = tokenizer.tokenize(text)
print('Tokens:', tokens)
token_ids = tokenizer.convert_tokens_to_ids(tokens)
print('Token IDs:', token_ids)
print('Vocab Size:', tokenizer.vocab_size)

def generate_embedding(text):
    if tokenizer is None:
        raise RuntimeError("Tokenizer is not initialized.")
    if model is None:
        raise RuntimeError("Model is not initialized.")

    tokens = tokenizer.tokenize(text)
    print('Tokens:', tokens)

    inputs = tokenizer(
        text,
        return_tensors="pd",
        padding=True,
        truncation=True,
        max_length=512,
        add_special_tokens=True,
    )

    # Debug: Print inputs
    print("Inputs:", inputs)

    # Validate token IDs
    token_ids = inputs['input_ids'].numpy()
    print("Token IDs:", token_ids)

    if np.any(token_ids < 0) or np.any(token_ids >= tokenizer.vocab_size):
        print(f"Invalid token IDs found. Vocab size: {tokenizer.vocab_size}")
        print(f"Token IDs: {token_ids}")
        raise ValueError("Invalid token IDs detected. Please check the tokenizer configuration and input text.")
    
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
metadata_store = {}  # Dictionary to store metadata against document ID
for doc in documents:
    print(f"Generating embedding for document: {doc['text']}")
    emb = generate_embedding(doc["text"])
    embeddings.append(emb)
    metadata_store[doc["id"]] = doc["metadata"]

# Convert embeddings to numpy array
embeddings_np = np.vstack(embeddings)

# Build FAISS index for similarity search
d = embeddings_np.shape[1]  # Dimension of embeddings
index = faiss.IndexFlatL2(d)  # Using L2 distance
index.add(embeddings_np)  # Add embeddings to FAISS index

# Function to search for similar documents using FAISS
def search_faiss(query_text, top_k=3):
    # Generate the embedding for the query text
    query_embedding = generate_embedding(query_text)
    
    # Perform the search on the FAISS index to find the top_k nearest neighbors
    D, I = index.search(query_embedding, top_k)
    
    # Initialize an empty list to store the search results
    results = []
    
    # Iterate over the indices of the nearest neighbors
    for i, idx in enumerate(I[0]):
        # Append the result as a dictionary containing the text, metadata, and distance
        results.append({
            "text": documents[idx]["text"],  # The text of the document
            "metadata": metadata_store[idx],  # The metadata of the document
            "distance": D[0][i]  # The distance between the query and the document
        })
    
    # Return the list of results
    return results

# Test the system with different queries
""" test_queries = [
    "菩萨如何发愿度众生，成就无上正等正觉？",
    "什么是佛性，众生因何迷失本性？",
    "如来成佛的无量功德是什么？",
    "四谛法门的具体内容是什么？",
    "量子力学研究的是什么？",
    "相对论如何改变了人类对宇宙的认识？",
    "人工智能如何模拟人类智能？",
    "深度学习如何解决复杂的模式识别问题？",
] """

test_queries = [
    "微观粒子",
]

# Run tests
for query in test_queries:
    print(f"Query: {query}")
    results = search_faiss(query)
    for result in results:
        print(f"Text: {result['text']}, Metadata: {result['metadata']}, Distance: {result['distance']:.4f}")
    print("-" * 50)
