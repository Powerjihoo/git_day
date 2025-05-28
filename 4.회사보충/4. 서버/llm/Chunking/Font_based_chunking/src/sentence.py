import fitz  # PyMuPDF
from itertools import groupby
from collections import Counter
from kiwipiepy import Kiwi
import json

kiwi = Kiwi()

def merge_spans_by_y(spans, mediabox):
    grouped_spans = groupby(sorted(spans, key=lambda span: round(span['origin'][1], 2)),
                            key=lambda span: round(span['origin'][1], 2))
    
    fontsize_counter = Counter(span["size"] for span in spans)

    # Find the most common fontsize
    common_fontsize = fontsize_counter.most_common(1)[0][0] if fontsize_counter else None
    
    # Filter spans that have the most common fontsize
    common_fontsize_spans = [span for span in spans if span["size"] == common_fontsize]
    
    merged_spans = []
    for y, group in grouped_spans:
        group = list(group)
        if group:
            first_span = group[0]
            last_span = group[-1]
            merged_spans.append({
                "y": y,
                "text": "".join(span["text"] for span in group),
                "x0": min(span["bbox"][0] for span in group),
                "x1": max(span["bbox"][2] for span in group),
                "y0": first_span["bbox"][1],
                "height": first_span["bbox"][3] - first_span["bbox"][1],
                "first_fontsize": first_span["size"],
                "first_font": first_span["font"],
                "last_fontsize": last_span["size"],
                "last_font": last_span["font"],
                "flags": first_span["flags"]
            })
    
    mediabox_width = mediabox.x1 - mediabox.x0
    merged_result = []
    x0_values = list(map(lambda span: span["bbox"][0], common_fontsize_spans))
    min_x0 = min(x0_values) if x0_values else 0
    i = 0
    while i < len(merged_spans):
        current_span = merged_result[i] if i < len(merged_result) else merged_spans[i]
        
        while i + 1 < len(merged_spans):
            next_span = merged_spans[i + 1]
            x1_diff = current_span["x1"] - mediabox.x0

            if next_span["flags"] == 1:
                next_span["first_fontsize"] = current_span["last_fontsize"]
                next_span["last_fontsize"] = current_span["last_fontsize"]
                next_span["x1"] = current_span["x1"]
            
            if round(x1_diff) >= round(mediabox_width - min_x0) and \
               (current_span["last_fontsize"] == next_span["first_fontsize"]):
                
                current_span["text"] += next_span["text"]
                current_span["x1"] = next_span["x1"]
                current_span["last_fontsize"] = next_span["last_fontsize"]
                current_span["last_font"] = next_span["last_font"]
                
                i += 1
            else:
                break
        
        merged_result.append(current_span)
        i += 1
    
    return merged_result

def extract_page_data(page):
    blocks = page.get_text("dict")["blocks"]
    
    spans = [
        span for block in blocks if "lines" in block
        for line in block["lines"]
        for span in line["spans"]
    ]
    
    mediabox = page.rect
    
    return merge_spans_by_y(spans, mediabox)

def most_common_fontsize(spans):
    if not spans:
        return 12
    
    fontsize_counter = Counter(span["first_fontsize"] for span in spans)
    most_common = fontsize_counter.most_common(1)
    return most_common[0][0] if most_common else 12

def split_text_into_sentences(text):
    """Split text into sentences and return a list of sentences."""
    sentences = text.split('. ')
    return [s.strip() for s in sentences if s.strip()]

# def process_pdf_file(file_path):
#     doc = fitz.open(file_path)
    
#     all_pages_data = []
    
#     for page in doc:
#         page_data = extract_page_data(page)
#         most_common_size = most_common_fontsize(page_data)
#         page_spans = []

#         for original_index, span in enumerate(page_data):
#             font_size = span["first_fontsize"]
            
#             if font_size == most_common_size:
#                 # Only split text into sentences for the most common font size
#                 original_text = span["text"]
#                 sentences = split_text_into_sentences(original_text)
                
#                 for idx, sentence in enumerate(sentences):
#                     new_span = span.copy()  # Copy the span to create a new one
#                     new_span["text"] = sentence
#                     new_span["origin_span_number"] = original_index + 1  # Store original span number
#                     new_span["title"] = None  # Initial title, will be set based on context
#                     new_span["changed_text"] = kiwi.space(sentence, reset_whitespace=True)
#                     new_span["page_number"] = page.number
#                     new_span["sentence_index"] = idx + 1
#                     page_spans.append(new_span)
#             else:
#                 # For other font sizes, keep the original span
#                 span["changed_text"] = kiwi.space(span["text"], reset_whitespace=True)
#                 span["title"] = None
#                 span["origin_span_number"] = original_index + 1  # Store original span number
#                 span["page_number"] = page.number
#                 page_spans.append(span)
        
#         # Apply title based on the most common font size
#         last_title = ""
#         for span in page_spans:
#             if span["first_fontsize"] > most_common_size:
#                 last_title = span["text"].strip()  # Update title for larger font sizes
#             elif span["first_fontsize"] == most_common_size:
#                 span["title"] = last_title
#             elif span["first_fontsize"] < most_common_size:
#                 span["title"] = last_title
        
#         all_pages_data.extend(page_spans)

#     doc.close()
    
#     sorted_data = sorted(all_pages_data, key=lambda x: (x["page_number"], x["y"]))
    
#     return sorted_data

def process_pdf_file(file_path):
    doc = fitz.open(file_path)
    
    all_pages_data = []
    last_title = ""  # 마지막 타이틀을 저장하는 변수
    last_page_number = None  # 마지막 페이지 번호
    last_font_size = None  # 마지막 폰트 크기
    last_changed_text = ""  # 마지막 변경된 텍스트
    
    for page in doc:
        page_data = extract_page_data(page)
        most_common_size = most_common_fontsize(page_data)  # 페이지에서 가장 많이 쓰인 폰트 크기
        page_spans = []

        for original_index, span in enumerate(page_data):
            font_size = span["first_fontsize"]
            
            if font_size == most_common_size:
                # 폰트 크기가 기본 폰트 크기인 경우 문장을 분리
                original_text = span["text"]
                sentences = split_text_into_sentences(original_text)
                
                for idx, sentence in enumerate(sentences):
                    new_span = span.copy()  # 기존 span을 복사해서 새로운 span 생성
                    new_span["text"] = sentence.strip()  # 공백 제거 후 저장
                    new_span["origin_span_number"] = original_index + 1  # 원래 span 번호 저장
                    new_span["title"] = None  # 초기 타이틀 값
                    new_span["changed_text"] = kiwi.space(sentence, reset_whitespace=True)
                    new_span["page_number"] = page.number
                    new_span["sentence_index"] = idx + 1
                    
                    # 공백이 아닌 텍스트만 추가
                    if new_span["text"]:
                        page_spans.append(new_span)
            elif font_size < most_common_size:
                # 폰트 크기가 기본 폰트 크기보다 작으면 부가 정보로 분류하여 삭제
                continue  # 부가 정보로 간주하고 삭제
            else:
                # 폰트 크기가 더 큰 경우 원본을 그대로 유지
                span["changed_text"] = kiwi.space(span["text"], reset_whitespace=True)
                # 만약 같은 페이지에서 이전 폰트가 더 크다면 이전 타이틀 유지
                if last_page_number == page.number and last_font_size and last_font_size > font_size:
                    span["title"] = last_changed_text  # 이전 변경된 텍스트를 타이틀로 사용
                else:
                    span["title"] = span["changed_text"]  # 현재 span의 변경된 텍스트를 타이틀로 설정
                    last_changed_text = span["changed_text"]  # 마지막 변경된 텍스트 업데이트
                
                # 나머지 속성 업데이트
                span["origin_span_number"] = original_index + 1  # 원래 span 번호 저장
                span["page_number"] = page.number
                
                # 공백이 아닌 텍스트만 추가
                if span["text"].strip():
                    page_spans.append(span)
                
                # 마지막 페이지 번호와 폰트 크기 업데이트
                last_page_number = page.number
                last_font_size = font_size

        # 타이틀 설정 (가장 많이 사용된 폰트 크기보다 큰 텍스트에 타이틀로 설정)
        tolerance = 1  # 허용 오차 범위 설정
        current_page_title_found = False
        for span in page_spans:
            fontsize = span["first_fontsize"]
            
            if abs(fontsize - most_common_size) <= tolerance:  # 폰트 크기 차이가 허용 오차 이내인 경우
                span["title"] = last_title  # 타이틀 설정
            elif fontsize > most_common_size + tolerance:
                last_title = span["text"].strip()  # 큰 폰트 크기를 타이틀로 설정
                current_page_title_found = True
            elif fontsize < most_common_size - tolerance:
                span["title"] = last_title  # 기본 폰트 크기 이하인 경우에도 최근 타이틀 사용

        # 만약 페이지에서 타이틀이 발견되지 않았으면, 이전 페이지의 last_title 사용
        if not current_page_title_found:
            for span in page_spans:
                span["title"] = last_title

        all_pages_data.extend(page_spans)

    doc.close()

    sorted_data = sorted(all_pages_data, key=lambda x: (x["page_number"], x["y"]))

    return sorted_data



def save_to_json(data, output_file):
    """Save the processed data to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def print_merged_data(merged_data, output_file):
    for data in merged_data:
        print(f"Page {data['page_number'] + 1}, y: {data['y']}, x0: {data['x0']}, x1: {data['x1']}, y0: {data['y0']}, height: {data['height']}, "
              f"First Fontsize: {data['first_fontsize']}, First Font: {data['first_font']}, "
              f"Last Fontsize: {data['last_fontsize']}, Last Font: {data['last_font']}, text: {data['text']}, "
              f"changed_text: {data['changed_text']}, title: {data.get('title', 'N/A')}")
        print("=================================\n")

    # Convert merged_data to a format suitable for JSON output
    json_data = []
    for data in merged_data:
        entry = {
            "page_number": data["page_number"],
            # "y": data["y"],
            # "x0": data["x0"],
            # "x1": data["x1"],
            # "y0": data["y0"],
            # "height": data["height"],
            # "first_fontsize": data["first_fontsize"],
            # "first_font": data["first_font"],
            # "last_fontsize": data["last_fontsize"],
            # "last_font": data["last_font"],
            "title": data.get("title", "N/A"),
            "text": data["text"],
            "changed_text": data["changed_text"],
            "origin_span_number": data.get("origin_span_number", "N/A")
        }
        json_data.append(entry)

    save_to_json(json_data, output_file)