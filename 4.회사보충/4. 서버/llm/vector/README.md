# Vectorize 

청킹된 파일에 대해 Dense / Sparse Vector를 생성하는 코드입니다.



## Docker

### 도커 이미지 빌드

```sh
docker build -t vectorize .
```



### Docker 컨테이너 실행

##### 사용

~~~bash
docker run -it --rm --gpus all \
    -v $(pwd):/app \
    vectorize <json_file> <model_name> <device>
~~~

- `<json_file>`: 처리할 JSON 파일의 경로입니다. 이 파일은 컨테이너 내부에서 접근 가능한 경로로 마운트되어야 합니다. 
- `<model_name>`: 사용할 사전 학습 모델의 이름입니다. 예를 들어, `intfloat/multilingual-e5-large`.
- `<device>`: GPU 또는 CPU로의 매핑. GPU를 사용할 경우 `cuda:0`과 같은 형식으로 작성. CPU를 사용 시 `cpu`



##### 예시

```sh
docker run -it --rm --gpus all \
    -v $(pwd):/app \
    vectorize temp.json intfloat/multilingual-e5-large cuda:0
```



##### 파일 권한 설정

- 컨테이너 실행 후, 파일 권한을 조정하여 사용자가 파일을 수정 및 이동할 수 있도록 합니다.

  `sudo chmod -R u+w .`



## python native 사용법

##### 설치

- `pip install -r requirements.txt`

##### 사용

```bash
python vectorize.py --file_path <json_file> --model_name <model_name> --device <device>
```



##### 예시

```bash
python vectorize.py --file_path ./test.json --model_name intfloat/multilingual-e5-large --device cuda:0

```

