from utils import text_with_space

def change_bbox(current_bbox, x, y):
    return (
        current_bbox[0],
        current_bbox[1],
        x,
        y
    )

def merge_spans_by_origin(spans, space, numbers_space):
    def merge_recursive(merged_spans, i):
        if i >= len(spans):
            return merged_spans
        
        current_span = spans[i]

        while i + 1 < len(spans):
            next_span = spans[i + 1]

            if int(current_span["origin"][1]) == int(next_span["origin"][1]):
                current_span["text"] += text_with_space(
                    current_span["text"], 
                    next_span["text"],
                    space, 
                    numbers_space
                )
                current_span["bbox"] = change_bbox(current_span["bbox"], next_span["bbox"][2], next_span["bbox"][3])
                i += 1
            else:
                break

        merged_spans.append(current_span)
        return merge_recursive(merged_spans, i + 1)

    return merge_recursive([], 0)