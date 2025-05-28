# hwp2md

- hwp 파일을 읽어서 html 혹은 md 파일로 변환하는 라이브러리 입니다.

## Docker 사용법

### 설치

- 도커 빌드

`docker build -t hwp2md .`

### 사용

- hwp2html
    - hwp 파일을 읽어서 html 파일로 변환합니다.
    ```
    docker run -it --rm \
        -v [INPUT_FILE]:/usr/src/app/input.hwp \
        -v $(pwd)/output:/usr/src/app/output/ \
        hwp2md hwp2html input.hwp output/[OUTPUT_FILE]
    ```

    - 예시) src/MOA_MOB.hwp를 output/output.html로 변환
    ```
    docker run -it --rm \
        -v $(pwd)/src/MOA_MOB.hwp:/usr/src/app/input.hwp \
        -v $(pwd)/output:/usr/src/app/output/ \
        hwp2md hwp2html input.hwp output/output.html
    ```

- html2md
    - html 파일을 읽어서 md 파일로 변환합니다.
    ```
    docker run -it --rm \
        -v [INPUT_FILE]:/usr/src/app/input.html \
        -v $(pwd)/output:/usr/src/app/output/ \
        hwp2md hwp2html input.html output/[OUTPUT_FILE]
    ```
    - 예시) output/output.html을 output/output.md로 변환
    docker run -it --rm \
        -v $(pwd)/output/output.html:/usr/src/app/input.html \
        -v $(pwd)/output:/usr/src/app/output/ \
        hwp2md html2md input.html output/output.md
    ```



## python native 사용법

### 설치

- `pip install -r requirements.txt`

### 사용

- hwp2html
    - hwp 파일을 읽어서 html 파일로 변환합니다.
    - `python hwp2html.py -h <입력 파일> -d <출력 파일>`
    ```
    NAME
        hwp2html.py

    SYNOPSIS
        hwp2html.py <flags>

    FLAGS
        -h, --hwp5path=HWP5PATH
            Default: 'MOA_MOB.hwp'
        -d, --destpath=DESTPATH
            Default: 'MOA_MOB.html'
        ```

- html2md
    - `python html2md.py -h <입력 파일> -m <출력 파일>`
    ```
    NAME
        html2md.py

    SYNOPSIS
        html2md.py <flags>

    FLAGS
        -h, --html_file=HTML_FILE
            Default: 'MOA_MOB.html'
        -m, --md_file=MD_FILE
            Default: 'MOA_MOB.md'
    ```