import os
import json
import numpy as np
import torch
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

def extract_content_from_json_file(json_path):
    """
    JSON 파일에서 'Chunk' 필드를 추출합니다.

    Args:
        json_path (str): JSON 파일의 경로.

    Returns:
        list: 추출된 컨텐츠 목록.
    """
    content_list = []
    with open(json_path, 'r', encoding='utf-8') as json_file:
        try:
            data = json.load(json_file)
            if isinstance(data, list):
                for item in data:
                    if "Chunk" in item:
                        content_list.append(item["Chunk"])
            elif isinstance(data, dict) and "Chunk" in data:
                content_list.append(data["Chunk"])
        except json.JSONDecodeError:
            print(f"Error reading JSON file: {json_path}")
    return content_list

def extract_all_content_from_directory(directory_path):
    """
    주어진 디렉토리 내의 모든 JSON 파일에서 'Chunk' 필드를 추출합니다.

    Args:
        directory_path (str): 디렉토리의 경로.

    Returns:
        list: 추출된 모든 컨텐츠 목록.
    """
    all_content = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                content_list = extract_content_from_json_file(json_path)
                all_content.extend(content_list)
    return all_content

def data2npy(total, tokenizer, model):
    """
    입력 문자열 목록을 E5 모델을 사용해 벡터화하여 npy 파일로 저장합니다.

    Args:
        total (list): 벡터화할 문자열 리스트.
        tokenizer: E5 모델과 함께 사용될 토크나이저.
        model: E5 모델.
    """
    def average_pool(last_hidden_state: Tensor) -> Tensor:
        return torch.mean(last_hidden_state[0], dim=0)
        
    total_embeddings = []
    
    for i in range(len(total)):
        input_ids = tokenizer("passage: "+total[i], return_tensors='pt', max_length=512)['input_ids'].to(model.device)
        
        with torch.no_grad():
            output = model(input_ids)
            single_embeddings = average_pool(output.last_hidden_state)
            
        total_embeddings.append(single_embeddings.cpu().numpy())
    
    print(f"Total embeddings: {len(total_embeddings)}")
        
    np.save('handcraft.npy', total_embeddings)
    with open('handcraft.json', 'w', encoding='utf-8') as output_file: 
        output_file.write(json.dumps(total, indent=4, ensure_ascii=False))

if __name__ == '__main__':
    #NOTE
    # JSON 파일이 있는 디렉토리 경로
    directory_path = 'hand'  # 디렉토리 경로를 여기에 입력하세요.
    all_content = extract_all_content_from_directory(directory_path)
    
    # E5 모델 로드 및 텍스트 데이터 벡터화
    model = AutoModel.from_pretrained('intfloat/multilingual-e5-large', device_map='cuda:5')
    tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large')
    
    # 데이터를 벡터화하여 저장
    data2npy(all_content, tokenizer, model)