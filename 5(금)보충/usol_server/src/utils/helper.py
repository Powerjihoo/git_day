import difflib


def find_similar_key(keys, target, n:int=2, cutoff: float = 0.5):
    # dictionary의 모든 키를 리스트로 가져오기
    if isinstance(keys, dict):
        keys = list(keys.keys())

    # target과 가장 비슷한 key 찾기
    close_matches = difflib.get_close_matches(target, keys, n=2, cutoff=cutoff)

    # 가장 비슷한 key 반환 (있으면)
    if close_matches:
        return close_matches[0]

    # 없으면 None 반환
    return None


def compare_dicts(dict1, dict2):
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        if len(dict1) != len(dict2):
            return False
        for key in dict1:
            if key not in dict2:
                return False
            if not compare_dicts(dict1[key], dict2[key]):
                return False
        return True
    else:
        return dict1 == dict2
