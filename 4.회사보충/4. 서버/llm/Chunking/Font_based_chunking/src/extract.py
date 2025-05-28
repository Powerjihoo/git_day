import fitz  # PyMuPDF
from merge import merge_spans_by_origin

def extract_spans(page, space, number_space):
    """페이지별 spans값 추출"""
    blocks = page.get_text("dict")["blocks"]
    
    spans = [
        span for block in blocks if "lines" in block
        for line in block["lines"]
        for span in line["spans"]
    ]
    
    return merge_spans_by_origin(spans, space, number_space)