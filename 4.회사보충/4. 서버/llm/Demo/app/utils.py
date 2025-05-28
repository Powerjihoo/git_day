import faiss, torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from kiwipiepy import Kiwi
import bm25s

kiwi = Kiwi()

def single_db_query(args):
    """
    단일 데이터베이스 쿼리 작업을 수행하여 주어진 쿼리에 대해 가장
    유사한 문서의 인덱스와 거리를 반환합니다.

    Args:
        args (tuple): 쿼리, 데이터베이스 및 데이터베이스 키를 포함하는 튜플.

    Returns:
        dict: 주어진 키에 해당하는 유사한 문서 인덱스와 거리를 담은 딕셔너리.
    """
    query, db, key = args
    index = faiss.IndexFlatIP(db.shape[-1])
    index.ntotal
    faiss.normalize_L2(db)
    index.add(db)
    faiss.normalize_L2(query)
        
    distance, idx = index.search(query, 3)
    result = {key: (idx[0], distance[0])}
    
    return result

def rag(query, db, document, tokenizer, model, database, bm):
    """
    RAG(Retrieval-Augmented Generation) 기법을 사용하여 주어진 쿼리에 대한
    관련 문서를 검색하고 결괏값을 반환합니다.

    Args:
        query (str): 검색할 쿼리 문자열.
        db (dict): 데이터베이스 배열을 담고 있는 딕셔너리.
        document (dict): 각각의 키에 대응하는 문서를 담은 딕셔너리.
        tokenizer: 모델과 함께 사용할 토크나이저 객체.
        model: 쿼리 임베딩에 사용할 모델.
        database (str): 검색할 데이터베이스의 이름.
        bm (dict): BM25 인덱스를 담고 있는 딕셔너리.

    Returns:
        dict: 검색된 문서들의 결괏값을 포함하는 딕셔너리.
    """
    
    def querying(query, tokenizer, model):
        """
        주어진 쿼리를 인코딩하고 임베딩을 생성합니다.

        Args:
            query (str): 인코딩할 쿼리 문자열.
            tokenizer: 사용될 토크나이저 객체.
            model: 임베딩 생성을 위한 모델 객체.

        Returns:
            Tensor: 생성된 임베딩.
        """
        input_ids = tokenizer("query: " + query, return_tensors='pt')['input_ids'].to(model.device)
        with torch.no_grad():
            output = model(input_ids)
            
        return torch.mean(output.last_hidden_state[0], dim=0)
    
    def sparse(query, database, bm):
        """
        BM25를 사용하여 주어진 쿼리의 관련 문서를 검색합니다.

        Args:
            query (str): 검색할 쿼리 문자열.
            database (str): 검색할 데이터베이스의 이름.
            bm (dict): BM25 인덱스를 담고 있는 딕셔너리.
        """
        retriever = bm[database]
        query = bm25s.tokenize(' '.join([token.form for token in kiwi.tokenize(query)]))
        results, score = retriever.retrieve(query, k=3)
        
        print(results)
        print(score)

    sparse(query, database, bm)
    
    
    print(query)
    query = querying(query, tokenizer, model).unsqueeze(dim=0).cpu().numpy().astype(np.float32)
    
    keys = [database]
    selected_docs = {t: "" for t in keys}
    
    with ThreadPoolExecutor(max_workers=3) as executor:    
        args = [(query, db[key].astype(np.float32), key) for key in keys]
        
        results = list(executor.map(single_db_query, args))
        print(results)
        
    doc = []

    for i, key in enumerate(keys):
        for j in reversed(range(3)):
            doc.append([{'id': results[i][key][0][j], 'text': document[key][results[i][key][0][j]]}])
            if results[i][key][1][j] > 0.80:
                selected_docs[key] += document[key][results[i][key][0][j]] + '\n'
    # print(selected_docs)
    print(doc)
    return selected_docs