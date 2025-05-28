import os
import json
import numpy as np
import torch
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from kiwipiepy import Kiwi
import bm25s
import argparse

def extract_content_from_json_file(json_path):
    content_list = []
    with open(json_path, 'r', encoding='utf-8') as json_file:
        try:
            data = json.load(json_file)
            if isinstance(data, list):
                for item in data:
                    if "content" in item:
                        content_list.append(item["content"])
            elif isinstance(data, dict) and "content" in data:
                content_list.append(data["content"])
        except json.JSONDecodeError:
            print(f"Error reading JSON file: {json_path}")
    return content_list

def data2npy(file_name, total, tokenizer, model):
    def average_pool(last_hidden_state: Tensor) -> Tensor:
        return torch.mean(last_hidden_state[0], dim=0)

    total_embeddings = []

    for text in total:
        input_ids = tokenizer("passage: " + text, return_tensors='pt', max_length=512, truncation=True)['input_ids'].to(model.device)

        with torch.no_grad():
            output = model(input_ids)
            single_embeddings = average_pool(output.last_hidden_state)

        total_embeddings.append(single_embeddings.cpu().numpy())

    npy_output_path = os.path.join('db', f'{file_name}.npy')
    json_output_path = os.path.join('db', f'{file_name}.json')

    np.save(npy_output_path, total_embeddings)
    with open(json_output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(json.dumps(total, indent=4, ensure_ascii=False))

def perform_bm25_indexing(file_name, json_path):
    kiwi = Kiwi()

    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    corpus = []
    for item in data:
        corpus.append(item)

    texts = [' '.join([token.form for token in kiwi.tokenize(text)]) for text in corpus]
    encoded_corpus = bm25s.tokenize(texts, stopwords=None, stemmer=None)

    retriever = bm25s.BM25()
    retriever.index(encoded_corpus)

    output_directory = os.path.join('bm25', file_name)
    os.makedirs(output_directory, exist_ok=True)

    retriever.save(output_directory, corpus=corpus)

def main(args):
    file_name = os.path.splitext(os.path.basename(args.file_path))[0]
    print(f"Processing file: {file_name}")  # Debug line
    all_content = extract_content_from_json_file(args.file_path)

    model = AutoModel.from_pretrained(args.model_name).to(args.device)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    data2npy(file_name, all_content, tokenizer, model)

    json_output_path = os.path.join('db', f'{file_name}.json')
    perform_bm25_indexing(file_name, json_output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a JSON file and perform BM25 indexing.')
    parser.add_argument('--file_path', type=str, required=True, help='Path to the input JSON file.')
    parser.add_argument('--model_name', type=str, default='intfloat/multilingual-e5-large', help='Pretrained model name.')
    parser.add_argument('--device', type=str, default='cuda:0', help='Device for model loading, e.g., "cuda:0".')

    args = parser.parse_args()
    main(args)