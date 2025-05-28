import fitz  # PyMuPDF
import os
import json

from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings

# 모델 설정
model_name = 'intfloat/multilingual-e5-large-instruct'
model_kwargs = {'device': "cuda:0"}
text_splitter = SemanticChunker(
    HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=70,
)

output_folder_path = './processed_json_files'  # JSON 파일을 저장할 새 폴더 경로
os.makedirs(output_folder_path, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

def process_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError('File not found')

    # PDF 파일 읽기
    input_file = extract_text_from_pdf(file_path)

    # 문서 청킹
    docs = text_splitter.create_documents([input_file])
    
    # 청킹된 문서를 JSON 파일로 저장
    chunks = [{'content': doc.page_content[:512]} for doc in docs]
    
    # JSON 파일 저장 경로
    new_filename = os.path.basename(file_path).replace(".pdf", "")
    json_path = os.path.join(output_folder_path, f"{new_filename}_chunked.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)
    
    return json_path
