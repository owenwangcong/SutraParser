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
#MODEL_NAME = "ernie-3.0-base-zh"
#MODEL_NAME = "ethanyt/guwenbert-base"
MODEL_NAME = "Qwen/Qwen2.5-1.5B"
#MODEL_NAME = "gpt2"

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
#tokenizer = ErnieTokenizer.from_pretrained(MODEL_NAME)
#model = ErnieModel.from_pretrained(MODEL_NAME)

#tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, force_download=True)
#model = AutoModel.from_pretrained(MODEL_NAME, force_download=True)

from paddlenlp.transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype="float16")
input_features = tokenizer("你好！请自我介绍一下。", return_tensors="pd")
outputs = model.generate(**input_features, max_length=128)
print(tokenizer.batch_decode(outputs[0], skip_special_tokens=True))

# Test the tokenizer
text = '菩萨发愿度众生彩电冰箱'
tokens = tokenizer.tokenize(text)
print('Tokens:', tokens)
token_ids = tokenizer.convert_tokens_to_ids(tokens)
print('Token IDs:', token_ids)
print('Vocab Size:', tokenizer.vocab_size)









