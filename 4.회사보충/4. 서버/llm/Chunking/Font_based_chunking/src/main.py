import os
import json
import argparse
from process_pdf import (
    process_pdf_by_line,
    filter_spans_for_output,
    save_spans_to_json,
    process_pdf_by_contents,
    filter_spans_for_output_by_contents
)
from sentence import (
    process_pdf_file,
    print_merged_data,
)

from sentence_merge import (
    process_json_file,
    print_title_merged_data,
    format_json_elements_to_chunk,
    save_json_data
)
from transformers import AutoTokenizer  # 모델 로드

def process_multiple_pdfs_in_directory(directory_path, output_file):
    tok = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large')
    BIGCHUNK_MAX_SIZE = 512  # 최대 토큰 크기 설정
    all_merged_data = []  # 모든 PDF 파일의 결과를 누적할 리스트
    chunk_counter = 1  # Chunk 고유 키 카운터

    for file_name in os.listdir(directory_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(directory_path, file_name)
            print(f"Processing: {file_path}")

            # 1. PDF 처리 및 텍스트 추출
            merged_data = process_pdf_file(file_path)
            temp_output_file = file_path.replace(".pdf", "_temp.json")
            print_merged_data(merged_data, temp_output_file)

            # 2. 임시 JSON 파일을 청크로 변환
            json_merged_data = process_json_file(temp_output_file)
            title_merged_file = temp_output_file.replace("_temp.json", "_title_merged.json")
            print_title_merged_data(json_merged_data, title_merged_file)

            # 3. 청크 크기에 맞게 데이터 포맷팅
            formatted_data = format_json_elements_to_chunk(title_merged_file, tok, BIGCHUNK_MAX_SIZE)

            # 4. 각 청크에 파일명 및 Chunk 구분 키 추가
            for chunk in formatted_data:
                all_merged_data.append({
                    'file_name': file_name,  # 파일 이름 추가
                    'chunk_id': f"Chunk_{chunk_counter}",  # 청크 구분 키
                    'chunk_content': chunk  # 청크 내용
                })
                chunk_counter += 1  # 청크 카운터 증가

            # 5. 임시 파일 제거 (선택 사항, 임시 파일을 지우고 싶다면 사용)
            os.remove(temp_output_file)
            os.remove(title_merged_file)

    # 최종적으로 하나의 JSON 파일에 병합된 데이터를 저장
    save_json_data(all_merged_data, output_file)

def save_json_data(data, output_file):
    # output_file 경로의 디렉토리가 존재하지 않으면 생성
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directory {output_dir} created.")

    # 데이터를 JSON 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    input_directory = os.getenv('INPUT_DIRECTORY')
    output_file = os.getenv('OUTPUT_FILE')
   
    # 여러 PDF 파일 처리 및 결과를 하나로 병합하여 저장
    process_multiple_pdfs_in_directory(input_directory, output_file)

    # 여러 PDF 파일 처리 및 결과를 하나로 병합하여 저장
    process_multiple_pdfs_in_directory(input_directory, output_file)

if __name__ == "__main__":
    main()
    