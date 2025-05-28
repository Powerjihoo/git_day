
# README.md

## 설치 방법

압축을 푼 후 실행하기 전에 다음 세 가지 라이브러리를 설치해야 합니다.

```bash
pip install PyMuPDF
pip install kiwipiepy
pip install transformers
```

## 사용 방법

이 프로젝트의 메인 파일은 `main.py`입니다. `main.py`의 `main` 함수에서 PDF 파일을 처리할 수 있습니다. 다음은 주요 기능에 대한 설명입니다:

### 0. 여러 PDF 파일 병합
- `process_multiple_pdfs_in_directory` 함수를 통해 한 디렉토리 내의 여러 PDF 파일을 처리하고, 그 결과를 하나의 JSON 파일로 병합합니다.
- 각 PDF 파일은 고유한 청크(`Chunk`) 단위로 병합되며, 청크 ID와 함께 파일명이 포함된 결과를 JSON 파일로 저장합니다.

### 1. PDF 처리 및 텍스트 추출
- `process_pdf_file` 함수를 통해 PDF 파일의 텍스트를 줄 단위로 추출합니다.
- 페이지 번호와 텍스트 내용이 저장되며, 텍스트 크기에 따라 부가적인 정보는 필터링 됩니다.
- **결과**는 PDF 파일에서 동일한 y값을 가진 텍스트를 한 줄로 간주하고, 그 순서대로 텍스트를 추출합니다.
- 페이지 번호와 함께 가장 빈도수가 높은 폰트 크기의 텍스트는 제목(`title`)으로 설정되며, 나머지 텍스트는 문장 단위로 추출됩니다.
- **결과물**에는 문장 단위로 띄어쓰기 처리가 된 텍스트(`changed_text`)와 원본 스팬 정보(`origin_span_number`)가 포함됩니다.
- **결과물**은 `print_merged_data` 함수를 통해 JSON 파일로 저장되며, 예시 파일명은 `(샘플 pdf 파일이름)_temp.json`입니다.

### 2. 임시 JSON 파일을 청크로 변환
- `process_json_file` 함수를 통해 j`(샘플 pdf 파일이름)_temp.json` 요소를 타이틀 별로 그룹화 합니다.
- **결과물**은 JSON 파일로 저장되며, 예시 파일명은 `(샘플 pdf 파일이름)_title_merged.json`입니다.

### 3. 청크 크기에 맞게 데이터 포맷팅
- `format_json_elements_to_chunk` 함수를 통해 `(샘플 pdf 파일이름)_title_merged.json`을 title과 문장들을 Chunk 형식에 맞춰 변환합니다.
- 임베딩 모델의 토크나이저 사용하여 각 토큰의 길이를 계산하며, 토큰 길이의 합이 max_length보다 적은 경우 합치고, 많을 경우 분할합니다.



## 실행 예시

1. PDF 파일들이 위치한 디렉토리 경로를 설정합니다.
2. 병합된 결과를 저장할 출력 파일 경로를 설정합니다.
3. `main.py` 파일을 실행하여 PDF 파일을 처리합니다.

```bash
cd 'Font_based_chunking\src'
python main.py
```

**예시 경로 설정:**
- PDF 파일 디렉토리 경로: `data/`
- 최종 출력 파일 경로: `data/output/final_merged_output.json`

## 주의사항

- PDF 파일 내에서 텍스트가 시작되는 기호에 따라 잘못된 정보로 분류될 수 있습니다.
- 청크 단위로 파일을 병합할 때, 최대 토큰 크기를 512로 설정하여 메모리 초과를 방지합니다.
