from process_pdf import process_pdf_by_line, process_spans_by_page_additional_info
from kiwipiepy import Kiwi

kiwi = Kiwi()

def process_pdf_file_mapped_filter(file_path):
    """PDF 문장 단위로 텍스트 추출, 부가 정보 삭제 및 origin_span_number 처리"""
    
    # 1. PDF에서 스팬 데이터 추출
    all_merged_spans = process_pdf_by_line(file_path)
    print(all_merged_spans)
    
    # 2. 부가 정보 기준 설정 (ascender, descender, fontsize)
    updated_spans = process_spans_by_page_additional_info(all_merged_spans)

    # 3. 문장 단위로 데이터를 생성하면서 부가 정보 삭제
    merged_data = []
    
    previous_page_number = None  # 이전 페이지 번호를 저장할 변수
    previous_y = None  # 이전 스팬의 y 좌표
    previous_fontsize = None  # 이전 스팬의 폰트 크기
    span_number = 0  # origin_span_number를 처리하는 변수 (페이지 전체에서 유일)
    current_title = ""  # 현재 타이틀을 저장할 변수

    for span in updated_spans:
        # 페이지가 바뀌면 original_index를 다시 0으로 초기화
        if span['page_number'] != previous_page_number:
            previous_page_number = span['page_number']
            previous_y = None  # 새 페이지에서 y 좌표 초기화
            previous_fontsize = None  # 새 페이지에서 폰트 크기 초기화
            current_title = ""  # 새로운 페이지에서는 타이틀 초기화

        # 스팬의 Y 좌표는 bbox에서 추출 (y0 값 사용)
        current_y = span['bbox'][1]  # bbox의 y0 값

        # 폰트 크기 가져오기 ('first_fontsize'가 없으면 'size'를 사용)
        current_fontsize = span.get('first_fontsize', span.get('size', None))

        # 같은 문단인지 확인 (y 좌표 차이가 5 이하이고, 폰트 크기가 동일한 경우 같은 문단으로 간주)
        if previous_y is not None and abs(current_y - previous_y) <= 5 and current_fontsize == previous_fontsize:
            # 같은 문단이면 span_number는 유지
            pass
        else:
            # 다른 문단이면 새로운 span_number를 부여
            span_number += 1

        # 현재 스팬의 y 좌표와 폰트 크기 저장
        previous_y = current_y
        previous_fontsize = current_fontsize

        # 타이틀 설정 (폰트 크기가 큰 경우 타이틀로 간주)
        if current_fontsize > previous_fontsize:
            current_title = span["text"].strip()

        # 'changed_text'가 없을 경우 'text' 사용
        span['changed_text'] = span.get('changed_text', span.get('text', ''))
        
        # 부가 정보를 찾아서 해당 텍스트를 삭제
        if 'additional_info' in span:
            for info in span['additional_info']:
                # 부가 정보 텍스트를 'changed_text'에서 삭제
                print(span)
                span['changed_text'] = span['changed_text'].replace(info['text'], '').strip()

        # 문장을 분리해서 처리하는 경우
        original_text = span['text']
        sentences = split_text_into_sentences(original_text)  # 문장 단위로 분리
        
        for idx, sentence in enumerate(sentences):
            new_span = span.copy()  # 기존 span 복사
            new_span["text"] = sentence
            new_span["changed_text"] = kiwi.space(sentence, reset_whitespace=True)
            new_span["page_number"] = span['page_number']
            new_span["origin_span_number"] = span_number  # 같은 문단이라면 같은 span_number 할당
            new_span["sentence_index"] = idx + 1  # 문장 인덱스는 1부터 시작

            # 최종 문장 데이터 추가 (부가 정보 삭제된 상태)
            merged_data.append({
                'page_number': new_span['page_number'],
                'title': new_span.get('title', ''),
                'text': new_span['text'].strip(),
                'changed_text': new_span['changed_text'].strip(),
                'origin_span_number': new_span.get('origin_span_number', None),
                'sentence_index': new_span.get('sentence_index', None)
            })

    return merged_data


def split_text_into_sentences(text):
    """문장을 분리하는 간단한 함수"""
    sentences = text.split('. ')
    
    # 빈 문자열이 포함되지 않도록 필터링
    return [s.strip() for s in sentences if s.strip()]
