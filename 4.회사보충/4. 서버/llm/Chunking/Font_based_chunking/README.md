# PDF 처리 및 병합

이 프로젝트는 여러 PDF 파일을 처리하여 JSON 형식으로 병합하는 도구입니다. PDF 파일의 텍스트를 추출하고, 특정 조건에 따라 청크로 변환하여 최종 결과를 생성합니다.



## Docker 

Docker를 사용하여 실행할 수도 있습니다:

### Docker 이미지 빌드

Docker 이미지를 빌드합니다:

```bash
docker build -t chunk .
```

### Docker 컨테이너 실행

다음 명령어로 Docker 컨테이너를 실행합니다:

##### 사용

```bash
docker run --rm -v $(pwd)/data:/app/data -e INPUT_DIRECTORY=./data -e OUTPUT_FILE=./data/output/final_merged_output.json chunk
```

> - `docker run`: Docker 컨테이너를 실행하는 명령어입니다.
>
> 
>
> - `--rm`: 컨테이너 실행이 종료되면 자동으로 컨테이너를 삭제하는 옵션입니다. 이는 실행 후 불필요하게 남아있는 컨테이너를 제거하여 디스크 공간을 절약하는 데 유용합니다.
>
> 
>
> - `-v $(pwd)/data:/app/data`: 볼륨 매핑 옵션으로, 호스트 시스템의 현재 디렉토리 내 `data` 폴더를 컨테이너의 `/app/data` 경로에 연결합니다. 이를 통해 컨테이너 내부에서 `data` 디렉토리에 접근할 수 있습니다.
>
> 
>
> - `-e INPUT_DIRECTORY=./data`: 환경 변수를 설정하는 옵션입니다. `INPUT_DIRECTORY`라는 환경 변수를 설정하여 PDF 파일을 처리할 입력 디렉토리를 지정합니다. 여기서는 `./data` 폴더가 입력 디렉토리로 지정됩니다.
>
> 
>
> - `-e OUTPUT_FILE=./data/output/final_merged_output.json`: 출력 파일 경로를 지정하는 환경 변수를 설정합니다. PDF 처리 및 병합 작업 후 생성될 JSON 파일의 경로를 `./data/output/final_merged_output.json`으로 지정합니다.
>
> - `chunk`: 실행할 Docker 이미지의 이름입니다. 이는 앞서 `docker build` 명령어를 통해 `chunk`라는 이름으로 빌드된 이미지를 의미합니다.



##### 예시

```
docker run --rm -v $(pwd)/data:/app/data -e INPUT_DIRECTORY=./data -e OUTPUT_FILE=./data/output/final_merged_output.json chunk
```

이 명령어는 `data/` 디렉토리 내의 PDF 파일을 처리하여 결과 JSON 파일을 생성합니다. Docker 환경을 사용하면 호스트 시스템에 대한 의존성을 줄일 수 있어 더욱 편리하게 사용할 수 있습니다.