# DEMO RUN

데모 실행을 위한 준비 단계입니다. 모든 실행과정은 현재 디렉토리(`./Demo`)에서 실행합니다.



## Step1. nvidia-docker container 설치

도커 환경 내 nvidia gpu사용을 위한 container 설치 [[LINK]](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

```bash
#cmd

distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```





## Step2. GAOM LLM

#### 1. GAON LLM Download

huggingface에 등록된 언어모델을 다운로드하기 위해, access token 발급과정이 필요합니다. 
먼저, [Human-Inspired AI Research & Gaon Platform Contract Research Center](https://huggingface.co/KU-HIAI-GAONPF)에 접근 가능한 계정을 통해 token을 발급받습니다.  [LINK](https://huggingface.co/docs/hub/security-tokens#how-to-manage-user-access-tokens)에서 발급 과정을 확인할 수 있습니다.

~~~bash
# cmd
# Download the KU-HIAI-GAONPF/gaon model
# huggingface-cli download KU-HIAI-GAONPF/gaon --local-dir <download_path> --token <access_token>
pip install huggingface_hub

huggingface-cli download KU-HIAI-GAONPF/gaon --local-dir ./gaon --token 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
~~~

설치 완료된 모델은 현재 디렉토리의 `./Demo/gaon`에서 확인 가능합니다.



### 2. 학습된 모델 사용 시

모델을 사용하려면 현재 디렉토리로 다운로드한 모델을 복사해 주세요.





## Step3. CheckList

`config.json`에서 언어 모델과 데이터베이스 경로를 설정해야 합니다. 이 설정 파일은 모델과 데이터베이스에 대한 경로와 파일 목록을 지정합니다.

~~~json
{
    "models": {
        "llm": "gaon",
        "retrieval": "intfloat/multilingual-e5-large"
    },
    "db": 
    {
    "dir":"./db",
    "file":["moamob","nuclear","operation", "handcraft"]
    },

    "bm25": 
    {
        "dir":"./bm25",
        "file":[
            "moamob", "nuclear", "operation", "handcraft" ]
    }
}
~~~

> **`models`**: 
>
>   \- `llm`: 사용할 언어 모델의 이름을 지정합니다. 여기서는 "gaon"을 사용합니다. (이전 설정한 경로 입력)
>   \- `retrieval`: 정보를 검색할 때 사용할 모델의 이름을 지정합니다. 예를 들어, "intfloat/multilingual-e5-large"와 같은 모델을 사용할 수 있습니다.
>
> 
>
> **`db`**:
>
>   \- `dir`: 데이터베이스 파일이 저장된 디렉토리의 경로를 지정합니다. 위의 예시에서는 `./db`로 설정되어 있습니다.
>   \- `file`: 데이터베이스에서 사용할 파일의 목록을 배열로 지정합니다. 여기서는 "moamob", "nuclear", "operation", "handcraft" 파일이 포함되어 있습니다.
>
> 
>
> - **`bm25`**:
>
>   \- `dir`: BM25 알고리즘을 사용할 때 관련된 파일이 저장된 디렉토리의 경로입니다. 위의 예시에서는 `./bm25`로 설정되어 있습니다.
>   \- `file`: BM25에서 사용할 파일의 목록을 배열로 지정합니다. DB와 동일한 파일 목록이 포함되어 있습니다. 확인 후 필요에 따라 조정할 수 있습니다.






## Step4. RUN

이제 모델을 실행할 준비가 되었으며 아래 두 가지 방법으로 실행할 수 있습니다.



#### 1. Python Native

가상환경을 설정한 후, 필요한 패키지를 설치하고 실행합니다.

```cmd
#가상환경 설정
pip install -r requirements.txt

#실행
python main.py
```



### 2. Docker

#### 2.1 이미지파일 생성

현재 디렉토리에서 존재하는 Dockerfile을 이용해 이미지를 생성합니다.

```bash
docker build -t demo .
```



#### 2.2 컨테이너 실행

이제 생성된 이미지를 바탕으로 컨테이너를 실행할 수 있습니다. 아래 명령어를 사용해 실행합니다.

```bash
docker run -p <호스트 포트>:<컨테이너 포트> -e FLASK_RUN_PORT=<flask 서버 포트> --gpus "all" --network host -v <현재 경로>:<옮길 경로> <image이름>
```

> 여기서 **`--gpus "all"`**을 사용하면 Docker는 사용 가능한 모든 GPU를 컨테이너에 연결합니다. 특정 GPU만 사용하고 싶다면, `--gpus '"device=0,1"'` 형식으로 원하는 GPU의 번호를 쉼표로 구분하여 지정할 수 있습니다.



예를 들어, Flask 서버 포트를 46986으로 설정하고, 현재 디렉토리를 `/app`으로 매핑하여 컨테이너를 실행하고자 할 경우, 다음과 같이 실행합니다:

```bash
docker run --rm -p 46986:46986 -e FLASK_RUN_PORT=46986 --gpus "0" --network host -v .:/app demo
```

| Argument                        | 설명                                                         |
| ------------------------------- | ------------------------------------------------------------ |
| `<호스트 포트>:<컨테이너 포트>` | 호스트와 컨테이너 간의 포트를 매핑합니다. 예를 들어, `46986:46986`으로 설정하면 호스트의 46986 포트가 컨테이너의 46986 포트로 매핑됩니다. |
| `FLASK_RUN_PORT`                | Flask 서버가 사용할 포트를 지정합니다. 예시로 46986을 사용할 수 있습니다. |
| `--gpus "0"`                    | 사용할 GPU의 ID를 지정합니다. 여러 개의 GPU가 있을 경우, 원하는 GPU의 ID를 입력하십시오. |
| `-v <현재 경로>:<옮길 경로>`    | 호스트의 현재 디렉토리를 컨테이너 내의 원하는 경로로 매핑합니다. 복사할 경로를 지정하세요. |
| `<image이름>`                   | 실행할 Docker 이미지의 이름입니다. 정확한 이미지 이름을 입력하세요. |