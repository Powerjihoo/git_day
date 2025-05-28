import json

# JSON 파일을 읽는 함수
def read_and_print_json(file_path):
    try:
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON 데이터 출력
        print(json.dumps(data, ensure_ascii=False, indent=4))
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

# JSON 파일 경로
file_path = 'teset_1.json'

# JSON 데이터 읽고 출력
read_and_print_json(file_path)
