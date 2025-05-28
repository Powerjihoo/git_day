## Chunk

다음은 청킹에 관한 소스들 입니다. 각각의 용도는 다음과 같습니다.
- hwp2md : 데이터를 html파일로 변환해주는 모듈입니다. 이를 기반으로 base_chunking이 진행됩니다.
- base_chunking : html 파일을 페이지별로 분할한 뒤, 이를 semantic기반 chunking을 진행하는 코드입니다. 이는 기초적인 청킹 코드입니다.
- font_based_chuking : font size를 기반으로 문서를 구조적으로 분석해 청킹하는 코드입니다. 가장 최신의 청킹 코드입니다.

## 유의점
각각이 의존성이 다르므로, 목적에 맞는 환경설치를 요합니다.