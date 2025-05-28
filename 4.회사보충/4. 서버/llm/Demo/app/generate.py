import json
from transformers import AutoTokenizer, AutoModel
import numpy as np
from vllm import LLM
import bm25s


def load_config():
    with open("config.json", "r") as file:
        return json.load(file)
        
class ModelManager:
    """
    모델 및 관련 리소스를 관리하는 클래스입니다. 다양한 모델과 토크나이저,
    데이터베이스, BM25 모델을 로드하고 접근할 수 있도록 기능을 제공합니다.
    """
    
    def __init__(self):
        """
        ModelManager 클래스의 초기화 메서드입니다.
        
        self.models: 모델 인스턴스를 저장하는 딕셔너리.
        self.tokenizers: 토크나이저 인스턴스를 저장하는 딕셔너리.
        self.db: 데이터베이스를 저장하는 딕셔너리.
        self.bm: BM25 인스턴스를 저장하는 딕셔너리.
        self.document: 데이터베이스에 관련된 문서 정보를 저장하는 딕셔너리.
        """
        self.models = {}
        self.tokenizers = {}
        self.db = {}
        self.bm = {}
        self.document = {}
    
    
    def load_model(self, model_name, gpu_id=None):
        """
        주어진 모델 이름으로 모델과 토크나이저를 로드합니다.

        Args:
            model_name (str): 로드할 모델의 이름입니다.
            gpu_id (int, optional): 사용할 GPU의 ID입니다. 
                                    기본값은 None입니다.
        """
        #NOTE: e5 모델 처리
        
        model = AutoModel.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        self.models[model_name] = model
        
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        
        self.tokenizers[model_name] = tokenizer

    def load_vllm(self, model_name):
        """
        VLLM 모델을 로드합니다.

        Args:
            model_name (str): 로드할 VLLM 모델의 이름입니다.
        """
        self.models[model_name] = LLM(model=model_name, dtype='float16')
         
         
        tokenizer = AutoTokenizer.from_pretrained(model_name,cached_dir=model_name)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        
        self.tokenizers[model_name] = tokenizer
        
    def get_model(self, model_name):
        """
        주어진 모델 이름에 해당하는 모델을 반환합니다.

        Args:
            model_name (str): 반환할 모델의 이름입니다.

        Returns:
            model: 요청한 이름에 해당하는 모델 객체.
                   존재하지 않으면 None을 반환합니다.
        """
        return self.models.get(model_name)
    
    def get_tokenizer(self, model_name):
        """
        주어진 모델 이름에 해당하는 토크나이저를 반환합니다.

        Args:
            model_name (str): 반환할 토크나이저의 이름입니다.

        Returns:
            tokenizer: 요청한 이름에 해당하는 토크나이저 객체.
                       존재하지 않으면 None을 반환합니다.
        """
        return self.tokenizers.get(model_name)
    
    def load_db(self, name):
        """
        주어진 이름에 해당하는 데이터베이스를 로드합니다.

        Args:
            name (str): 로드할 데이터베이스의 이름입니다.
        """
        # NOTE: 데이터베이스 로드
        path=load_config()['db']['dir']
        db_path = f"{path}/{name}"  # JSON에서 디렉토리 경로 가져오기
        self.db[name] = np.load(f'{db_path}.npy')
        with open(f'{db_path}.json', mode='r') as reader:
            self.document[name] = json.load(reader) 
        
    def load_bm(self, name):
        """
        주어진 이름에 해당하는 BM25 모델을 로드합니다.

        Args:
            name (str): 로드할 BM25 모델의 이름입니다.
        """
        #NOTE: BM25 모델 로드
        path=load_config()['bm25']['dir']
        bm_path = f"{path}/{name}"  # JSON에서 디렉토리 경로 가져오기
        self.bm[name] = bm25s.BM25.load(bm_path, load_corpus=True)
        
model_manager = ModelManager()

def initialize_models():
    """
    모델과 관련된 데이터베이스 및 BM25 모델을 초기화 및 로드합니다.
    """
    
    #NOTE: VLLM 및 다른 모델 초기화
    config=load_config()
    
    for key,model_name in config["models"].items():
        if 'llm' == key:
            model_manager.load_vllm(model_name)
        else: model_manager.load_model(model_name)    
        
    # Dense 데이터베이스 로드
    for db_name in config["db"]['file']:
        model_manager.load_db(db_name)
        # model_manager.load_db('moamob')
        # model_manager.load_db('nuclear')
        # model_manager.load_db('operation')
        # model_manager.load_db('handcraft')
     
    # BM25 모델 로드   
    for bm_name in config["bm25"]['file']:
        model_manager.load_bm(bm_name)
        # model_manager.load_bm('moamob')
        # model_manager.load_bm('nuclear')
        # model_manager.load_bm('operation')
        # model_manager.load_bm('handcraft')