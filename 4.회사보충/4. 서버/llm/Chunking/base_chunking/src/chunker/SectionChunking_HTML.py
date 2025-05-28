import os
from bs4 import BeautifulSoup
import json
from transformers import AutoTokenizer

# 사용할 모델의 이름을 지정합니다.
model_name = "intfloat/multilingual-e5-large-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 처리할 최상위 폴더 경로 지정
top_folder_path = 'data/data_100/100_version_new'

# 폴더 내의 모든 XHTML 파일 경로 재귀적으로 찾기
file_paths = []
for root, dirs, files in os.walk(top_folder_path):
    for file_name in files:
        if file_name.endswith('.xhtml'):
            file_paths.append(os.path.join(root, file_name))

for file_path in file_paths:
    # 파일 경로에서 최상위 폴더 다음의 폴더 이름을 index로 사용
    relative_path = os.path.relpath(file_path, top_folder_path)
    folder_name = relative_path.split(os.sep)[0]
    original_file_name = os.path.basename(file_path).split(".")[0]
    print(f"Processing {original_file_name} in folder {folder_name}")

    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')

    # 스타일 정보 추출
    styles = soup.find_all('style')
    style_text = [style.text for style in styles]

    # 메타 데이터 추출
    metadata = [meta.attrs for meta in soup.find_all('meta')]

    # 'div' 태그 청킹: 'class' 속성이 'Section-*'인 div 태그를 기준으로 청킹
    sections = soup.find_all('div', class_=lambda value: value and value.startswith('Section-'))
    section_texts = [section.text.strip() for section in sections]

    # 'Section-X' 클래스를 갖는 모든 div 태그 추출
    sections = soup.find_all('div', class_=lambda value: value and value.startswith('Section-'))

    sections_list = []
    # 각 섹션의 텍스트 출력 및 청킹
    for index, section in enumerate(sections):
        print("\n\n")
        print(f"### Section {index + 1} content:")
        print(section.text)
        tokens = tokenizer.encode(section.text, add_special_tokens=True)
        token_length = len(tokens)
        
        if token_length > 480:
            # 텍스트를 480 토큰 단위로 분할
            split_texts = [section.text[i:i+480] for i in range(0, len(section.text), 480)]
            for part_index, part_text in enumerate(split_texts):
                each_section = f"## {folder_name}\n### Section {index + 1}_Part {part_index + 1}\n{part_text}"
                sections_list.append(each_section)
        else:
            each_section = f"## {folder_name}\n### Section {index + 1}\n{section.text}"
            sections_list.append(each_section)

    # 각 섹션의 텍스트로 JSON 객체 리스트 생성
    chunks = [{'content': section} for section in sections_list]

    # JSON 데이터를 파일로 저장
    output_json_path = os.path.join(top_folder_path, 'details', f'{folder_name}.json')
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(chunks, json_file, ensure_ascii=False, indent=4)
