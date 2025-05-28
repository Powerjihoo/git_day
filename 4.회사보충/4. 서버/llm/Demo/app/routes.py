from flask import Blueprint, request, render_template
from .generate import model_manager
import torch
from .utils import *
from vllm import SamplingParams
from. generate import load_config

main = Blueprint('main', __name__)

def predict_model(llm_name, input_text, database,retrieval_name):
    """
    주어진 모델을 사용하여 입력 텍스트에 대한 예측을 수행합니다. 
    선택적으로 데이터베이스에서 문서를 가져와 예측에 사용합니다.

    Args:
        model_name (str): 예측에 사용할 모델의 이름입니다.
        input_text (str): 예측에 사용할 입력 텍스트입니다.
        database (str): 검색에 사용할 데이터베이스의 이름입니다.

    Returns:
        dict: 예측 결과 및 관련 정보를 포함하는 딕셔너리입니다.
    """
    model = model_manager.get_model(llm_name)
    tokenizer = model_manager.get_tokenizer(llm_name)
    db = model_manager.db
    document = model_manager.document
    bm = model_manager.bm
    
    if database == 'none':
        documents = {}
        documents['none'] = ''
    else:
        documents = rag(input_text, db, document, model_manager.get_tokenizer(retrieval_name), model_manager.get_model(retrieval_name),database,bm)
    
    prompts = {}
    keys = [database]
    
    for key in keys:
        if documents[key] == '':
            prompts[key] = tokenizer.apply_chat_template([{"role": "user", "content": f"{input_text}"}], tokenize=False, add_generation_prompt=True)
        else:
            prompts[key] = tokenizer.apply_chat_template([{"role": "user", "content": f'{documents[key]}\n{input_text}'}], tokenize=False, add_generation_prompt=True)
    
    # 개별적으로 인코드
    input_ids_list = []
    for key in keys:
        prompt = prompts[key]
        inputs = tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=False)
        input_ids_list.append(inputs.tolist()[0])
        
    with torch.no_grad():          
        #NOTE Generation parameters  
        output = model.generate(prompt_token_ids=input_ids_list, sampling_params=SamplingParams(max_tokens=384, temperature=0.3, top_p=0.95))
        
    # 디코드하여 결과 생성
    decoded_outputs = {
        keys[idx]: {
            'document': documents[keys[idx]],
            'output': output[idx].outputs[0].text,
            'database': database,
            'query': input_text
        }
        for idx in range(len(output))
    }
        
    return decoded_outputs

# NOTE: 메인 루트 엔드포인트
@main.route("/", methods=["GET", "POST"])
def index():
    """
    웹 애플리케이션의 메인 엔드포인트입니다. 
    사용자가 입력한 텍스트를 이용하여 모델 예측을 수행하고 결과를 반환합니다.

    Returns:
        템플릿 렌더링 결과 (HTML 페이지)
    """
    if request.method == "POST":
        input_text = request.form.get("text")
        database = request.form.get("database")
        
        if input_text == '':
            return render_template('index.html', results=None)
        
        llm_name=load_config()['models']['llm']
        retrieval_name=load_config()['models']['retrieval']
        
        output_text = predict_model(llm_name, input_text, database, retrieval_name)
        
        return render_template("index.html", input_text=input_text, results=output_text)

    return render_template("index.html", results=None)

