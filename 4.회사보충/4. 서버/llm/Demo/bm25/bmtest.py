#%%
'''
save
'''
import json
from kiwipiepy import Kiwi
import bm25s

kiwi = Kiwi()

# JSON 파일에서 데이터 로드
path = 'db/operation.json'
with open(path, 'r', encoding='utf-8') as file:
    handcraft_data = json.load(file)

# 문서 데이터를 가져옵니다.
corpus = []
for item in handcraft_data:
    corpus.append(item)

# 텍스트를 토크나이징
texts = [' '.join([token.form for token in kiwi.tokenize(text)]) for text in corpus]
encoded_corpus = bm25s.tokenize(texts, stopwords=None, stemmer=None)

# BM25로 인덱싱
retriever = bm25s.BM25()
retriever.index(encoded_corpus)

# 인덱스를 파일에 저장
path = path.split('/')[1].rstrip('.json')
retriever.save(path, corpus=corpus)

#%%

'''
load & retrieve
'''

from kiwipiepy import Kiwi
import bm25s

kiwi = Kiwi()

# 저장된 BM25 인덱스를 로드
path = "bm25/operation"
reloaded_retriever = bm25s.BM25.load(path, load_corpus=True)

# 검색할 쿼리 텍스트 정의
query = "정상 가동 중지 절차는 무엇인가요?"
query_tokens = bm25s.tokenize(' '.join([token.form for token in kiwi.tokenize(query)]))

# 쿼리에 대해 검색 수행
results, scores = reloaded_retriever.retrieve(query_tokens, k=3)

# 결과 출력
print(results[0])
print(scores[0])