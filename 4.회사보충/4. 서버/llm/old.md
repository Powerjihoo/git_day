# GAON
## 프로젝트 개요 (Introduction)
- GAON-LLM은 계약연구센터(가온플랫폼, 고려대)에서 개발한 한국어 대규모 언어 모델 프레임워크로, SaaS LLM(Software-as-a-Service based on Large Language Models) 또는 LLM 납품을 위한 원천기술 연구를 목표로 합니다.

## 시스템 아키텍처 (System Architecture)
![System Architecture](./assets/System%20Architecture.png)

## 소스 구조(Project Structure)
프로젝트는 다음과 같은 주요 구성 요소로 나뉩니다:
- Chunking: 데이터 분할 및 전처리
- Embedding: 텍스트 임베딩 처리
- LLM: 대규모 언어 모델 로직
- Demo (WEB): 웹 기반 데모 인터페이스

## Flow
프로젝트는 다음의 순서를 따릅니다:
1. Font_based_Chunking: 주어진 데이터를 분할 및 전처리 합니다.
2. Demo: Web Demo에서 청킹된 데이터를 기반으로 QA를 처리합니다.



</div>


## 기술 스택 (Tech Stack)
- 언어: Python
- 프레임워크: Hugging Face Transformers
- 모델: Gemma-ko
- 학습 데이터셋: 기술과학 문서 기계독해 데이터, dolly-ko
- 테스트 데이터셋: 가온 데이터셋(MOA_A+MOA_B , 가온 추가 Non_table 데이터)

## 문의 (Contact)
프로젝트와 관련된 문의는 [tlswndals13@korea.ac.kr]로 연락해 주세요.
