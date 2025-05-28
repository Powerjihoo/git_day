import fitz  # PyMuPDF
import json
from extract import extract_spans
from collections import Counter, defaultdict

def save_spans_to_json(spans, output_file):
    """스팬 데이터를 JSON 파일로 저장"""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(spans, file, ensure_ascii=False, indent=4)

def filter_spans_for_output(spans):
    """필요한 필드만 추출하여 새로운 리스트 반환"""
    return [{'text': span["text"]} for span in spans]

def filter_spans_for_output_by_contents(spans):
    filtered_spans = []
    
    for span in spans:
        span_output = {
            'page': span["page_number"],
            'text': span["text"]
        }

        # 'additional_info'가 존재하고, 그 값이 비어 있지 않은지 확인
        if "additional_info" in span and span["additional_info"]:
            additional_texts = [info["text"] for info in span["additional_info"] if "text" in info]
            if additional_texts:
                span_output['additional_info'] = additional_texts

        filtered_spans.append(span_output)

    return filtered_spans

def debug_spans(spans):
    """디버그 옵션이 켜져 있을 때 스팬 데이터를 출력"""
    for span in spans:
        print(span)

# # merge_option_space : span merge 할 때 space 추가 여부
# # merge_option_consecutive_numbers_space : span merge 할 때 앞 text 마지막과 뒤 text 처음이 숫자라면 space 추가할 지 여부
def process_pdf_by_line(file_path, merge_option_space=False, merge_option_consecutive_numbers_space=True, debug=True):
    """PDF를 처리하고 스팬 데이터를 JSON 파일로 저장"""
    doc = fitz.open(file_path)
    
    all_merged_spans = []
    
    """페이지 기준으로 spans값 merge"""
    for page in doc:
        spans = extract_spans(page, merge_option_space, merge_option_consecutive_numbers_space)
        # 각 span 사전에 page 번호 및 추가
        for span in spans:
            span["page_number"] = page.number
            span["mediabox"] = page.mediabox
        all_merged_spans.extend(spans)
    
    doc.close()

    if debug:
        debug_spans(all_merged_spans)

    return all_merged_spans

def find_most_common_asc_desc(spans):
    """각 페이지에서 가장 많이 나오는 ascender, descender 쌍을 찾는 함수"""
    asc_desc_pairs = [(span['ascender'], span['descender']) for span in spans]
    most_common_pair, _ = Counter(asc_desc_pairs).most_common(1)[0]
    return most_common_pair

def filter_spans_by_asc_desc(spans, most_common_pair, most_common_fontsize):
    """가장 많이 나오는 ascender, descender 쌍과 다른 스팬의 텍스트와 폰트크기를 필터링하는 함수"""
    return [
        {
            'text': span['text'],
            'fontsize': span['size']
        } 
        for span in spans if (span['ascender'], span['descender']) != most_common_pair and span['size'] < most_common_fontsize
    ]

def find_most_common_fontsize(spans):
    """가장 많이 나오는 fontsize를 찾는 함수"""
    font_sizes = [span['size'] for span in spans]
    most_common_size = Counter(font_sizes).most_common(1)
    return most_common_size[0][0] if most_common_size else None

def process_spans_by_page_additional_info(all_merged_spans):
    """페이지별로 ascender, descender 쌍을 분석하고, 결과를 처리하는 함수"""
    pages = defaultdict(list)

    # 페이지별로 스팬을 그룹화
    for span in all_merged_spans:
        pages[span['page_number']].append(span)

    # 새로운 스팬 리스트를 저장할 리스트
    updated_spans = []

    for page_number, spans in pages.items():
        most_common_pair = find_most_common_asc_desc(spans)
        most_common_fontsize = find_most_common_fontsize(spans)
        filtered_spans = filter_spans_by_asc_desc(spans, most_common_pair, most_common_fontsize)

        # 기존 spans에서 filtered_spans를 제거하고, 나머지에 부가 정보를 추가
        for span in spans:
            if any(span['text'] == filtered_span['text'] and span['size'] == filtered_span['fontsize'] for filtered_span in filtered_spans):
                # filtered_spans에 있는 span은 제거
                continue
            else:
                # filtered_spans 내용을 부가 정보로 추가
                span['additional_info'] = filtered_spans
                updated_spans.append(span)

    return updated_spans

def process_pdf_by_contents(file_path, merge_option_space=False, merge_option_consecutive_numbers_space=True, debug=False):
    all_merged_spans = process_pdf_by_line(file_path, merge_option_space, merge_option_consecutive_numbers_space, debug)

    # 부가 정보 분리
    update_spans = process_spans_by_page_additional_info(all_merged_spans)

    return update_spans