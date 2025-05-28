# 여기부턴 중민 작성

import json
from collections import defaultdict

# JSON 데이터를 순차적으로 읽고 title과 span_number 기준으로 문장을 병합하는 함수
def process_json_file(file_path):
    try:
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        grouped_data = []  # 최종적으로 그룹화된 데이터를 저장할 리스트
        current_group = None  # 현재 진행 중인 그룹

        # JSON 데이터를 순차적으로 순회
        for item in data:
            title = item.get('title', "")
            span_number = item.get('origin_span_number', None)
            changed_text = item.get('changed_text', '')  # changed_text를 사용
            
            # span_number가 None이면 스킵
            if span_number is None:
                continue

            # 새로운 title이 등장하면, 이전 그룹을 저장
            if current_group is None or current_group["title"] != title:
                # 현재 그룹이 있으면 저장, 단 다음 경우 제외:
                # 1. title이 null/""이고 문장이 하나일 경우
                # 2. title과 문장이 하나인 문장이 동일할 경우
                if current_group:
                    if not (current_group["title"] in [None, ""] and len(current_group["span_accumulator"]) == 1) and \
                       not (len(current_group["span_accumulator"]) == 1 and current_group["span_accumulator"][0]["text"] == current_group["title"]):
                        grouped_data.append(current_group)
                
                # 새로운 그룹 시작
                current_group = {
                    "title": title,
                    "sentences": [],
                    "span_accumulator": []  # 같은 span_number를 가진 문장들을 병합하기 위한 리스트
                }

            # 같은 span_number에 대해 문장 이어붙이기
            if current_group["span_accumulator"] and current_group["span_accumulator"][-1]["span_number"] == span_number:
                # 같은 span_number면 문장을 이어붙임
                current_group["span_accumulator"][-1]["text"] += " " + changed_text
            else:
                # 새로운 span_number면 새로 추가
                current_group["span_accumulator"].append({
                    "span_number": span_number,
                    "text": changed_text
                })

        # 마지막 그룹 저장, 단 제외 조건을 만족하지 않는 경우만 저장
        if current_group:
            if not (current_group["title"] in [None, ""] and len(current_group["span_accumulator"]) == 1) and \
               not (len(current_group["span_accumulator"]) == 1 and current_group["span_accumulator"][0]["text"] == current_group["title"]):
                grouped_data.append(current_group)
        
        return grouped_data

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None

# 그룹화된 데이터를 title과 sentence 번호로 병합하여 출력하고 저장하는 함수
def print_title_merged_data(grouped_data, output_file):
    try:
        result = []

        # 각 그룹에 대해 처리
        for group in grouped_data:
            # 만약 title이 None이면 첫 번째 문장을 title로 설정
            if group["title"] is None and group["span_accumulator"]:
                first_sentence = group["span_accumulator"][0]["text"].strip()
                group["title"] = first_sentence

            merged_group = {
                "title": group["title"],
                "sentences": {}
            }

            sentence_count = 1  # sentence 번호

            # 병합된 문장들을 sentence로 저장
            for item in group["span_accumulator"]:
                merged_group["sentences"][f"sentence {sentence_count}"] = item["text"].strip()
                sentence_count += 1

            result.append(merged_group)
        
        # 병합된 데이터를 JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"병합된 데이터가 {output_file}에 저장되었습니다.")
    
    except Exception as e:
        print(f"파일 저장 중 오류가 발생했습니다: {e}")


# 데이터를 그룹화하여 병합하는 함수
def group_lengths(lengths, max_size):
    groups = []
    current_group = []
    current_length = 0

    for i, length in enumerate(lengths):
        if current_length + length > max_size:
            groups.append(current_group)
            current_group = [i]
            current_length = length
        else:
            current_group.append(i)
            current_length += length

    if current_group:
        groups.append(current_group)

    return groups

# 토큰의 개수가 최대 512가 넘는 경우, Chunk를 분할하는 함수
def split_chunk_if_needed(chunk, tokenizer, max_size):
    sentences = chunk.split('\n')  # 문장 단위로 나눔
    current_chunk = []
    split_chunks = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(tokenizer.tokenize(sentence))  # 문장 길이를 토큰 단위로 계산
        if current_length + sentence_length > max_size:
            split_chunks.append("\n".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        split_chunks.append("\n".join(current_chunk))

    return split_chunks

# title과 문장들을 Chunk 형식에 맞춰 변환하는 함수
def format_json_elements_to_chunk(data, tokenizer, max_size):
    # data가 파일 경로인지, JSON 객체인지 확인
    if isinstance(data, str):
        # 파일 경로일 경우, 파일을 읽어 JSON 데이터를 로드
        with open(data, 'r', encoding='utf-8') as f:
            grouped_data = json.load(f)
    elif isinstance(data, dict) or isinstance(data, list):
        # JSON 객체일 경우, 그대로 사용
        grouped_data = data
    else:
        raise ValueError("잘못된 입력: JSON 파일 경로이거나 JSON 객체여야 합니다.")

    formatted_data = []

    # 각 그룹을 순회하며 title과 문장들을 처리
    for group in grouped_data:
        title = group.get("title", "")
        sentences = [sentence.strip() for sentence in group.get("sentences", {}).values()]
        formatted_sentences = "\n".join(sentences)

        # Chunk로 변환 (여기서 chunk가 문자열인지 확인)
        chunk = f"# title : {title}\n\n## context : {formatted_sentences}"
        
        if not isinstance(chunk, str):
            chunk = str(chunk)  # chunk가 문자열이 아닌 경우, 문자열로 변환

        # 각 Chunk의 토큰 길이를 계산
        tokenized_length = len(tokenizer.tokenize(chunk))

        if tokenized_length > max_size:
            # Chunk를 분할하는 경우
            split_chunks = split_chunk_if_needed(formatted_sentences, tokenizer, max_size)

            for i, split_chunk in enumerate(split_chunks):
                new_title = f"{title}_{i + 1}"  # title을 title_1, title_2로 변경
                formatted_data.append({"Chunk": f"# title : {new_title}\n## context : {split_chunk}"})
        else:
            # 그대로 추가
            formatted_data.append({"Chunk": chunk})

    # 각 Chunk의 토큰 길이를 계산
    lengths = [len(tokenizer.tokenize(chunk["Chunk"])) for chunk in formatted_data]

    # 그룹을 나누어 병합 처리
    grouped_chunks = group_lengths(lengths, max_size)

    # 각 그룹의 Chunk들을 두 줄 간격으로 병합
    new_data = [{'Chunk': "\n\n".join([formatted_data[idx]['Chunk'] for idx in group])} 
                for group in grouped_chunks]

    return new_data

# 변환된 데이터를 JSON 파일로 저장하는 함수
def save_json_data(formatted_data, output_file):
    try:
        # JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=4)
        print(f"데이터가 {output_file}에 JSON 형식으로 저장되었습니다.")

    except Exception as e:
        print(f"파일 저장 중 오류가 발생했습니다: {e}")