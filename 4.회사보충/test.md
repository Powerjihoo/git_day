# 경력기술서

## 요약
산업 데이터 기반 시계열 이상탐지 및 예측 시스템을 설계·운영한 엔지니어입니다.  
Python, Kafka, InfluxDB, Redis, PostgreSQL 기반 데이터 파이프라인 및 모델 운영 경험을 보유하고 있으며,  
Residual 기반 이상탐지, Threshold 자동계산, 모델 버전관리, 실시간 API 서비스 구현까지 수행했습니다.  
또한 시계열 모델(AAKR, ARIMA, VAE, ANNOY, ICA)에 대한 교육자료 제작 및 문서화를 통해 팀 역량 강화를 주도했습니다.

---

## 보유 기술 스택
- 언어: Python, SQL  
- 데이터/모델링: AAKR, ARIMA, VAE, ANNOY, ICA, LSTM, Prophet  
- 인프라/메시징: Kafka, Redis, InfluxDB, PostgreSQL  
- 환경: Linux(Ubuntu), Docker, WSL, Windows 가상환경(NSSM)  
- 협업: Git, JIRA, Notion, Swagger, FastAPI, WebSocket  

---

## 주요 프로젝트 경험

### 유솔 – 누수음 분류기 구축 (2023.05 ~ 2023.12)
- **목표**: AI 기반 누수음 분석으로 탐사 정확도 향상 및 비용 절감, 전문 인력 의존도 축소  
- **역할/업무**: FFT 데이터 수집/전처리, 5개 Type 분류, Labeling 및 모델 학습  
- **성과**: Accuracy 82%, F1 Score 0.87, TTA 인증 완료  
- **기술 스택**: Python, Numpy, Scikit-learn, FFT  

### 동서발전 – 발전소 데이터 상관관계 분석 (2023.08 ~ 2023.10)
- **목표**: 발전소 GT7, GT8, BOP 설비 데이터의 상관관계 분석 및 변수 그룹화  
- **역할/업무**: 상관관계 분석, Description 기반 변수 그룹화  
- **성과**: 센서 Description 기반 그룹화 기준 마련 → 모델링 데이터셋 설계에 활용  
- **기술 스택**: Python, Pandas, Numpy  

### 예천양수 – 발전소 이상탐지 시스템 구축 (2024.01 ~ 2025.02)
- **목표**: 514개 Tag 데이터 기반 이상탐지 시스템 구축  
- **역할/업무**: 상관관계 분석 → 74개 모델 그룹 분류, Residual 기반 이상탐지 문서화 및 성능평가  
- **성과**: 독립 투입 프로젝트로 전 과정 전담, Residual 기반 탐지 체계 정립, 모델 단순화(514→74)  
- **기술 스택**: Python, PostgreSQL, InfluxDB, Kafka, Swagger, VAE  

### ForeCast Trend – 열화상 데이터 기반 예측 시스템 (2024.08 ~ 2025.02)
- **목표**: 열화상 데이터로 30분 후 이상 발생 여부 예측  
- **역할/업무**: Resampling(5초→1분), ARIMA/Prophet/LSTM 성능 비교 후 ARIMA 채택, FastAPI+WebSocket 실시간 처리  
- **성과**: 30분 예측 성능 최적화, TTA 인증 완료  
- **기술 스택**: Python, ARIMA, Prophet, LSTM, FastAPI, WebSocket, PostgreSQL, InfluxDB  

### Script Server – 사용자 정의 스크립트 관리 시스템 개선 (2024.12 ~ 진행 중)
- **목표**: 관리자들이 직접 Script를 등록하여 알람/모델 학습에 활용할 수 있는 기능 개선  
- **역할/업무**: API 통합(Create/Delete/Update), Output Tag DB 저장/조회, Script_id→Script_name 매핑  
- **성과**: 미완성 서버를 안정화, 현업 관리자들이 직접 활용 가능한 수준으로 개선  
- **기술 스택**: Python, FastAPI, PostgreSQL, InfluxDB, Kafka  

### IPCM – Training/Algorithm Server 기능 개발 (2025.02 ~ 진행 중)
- **목표**: 회사 주력 제품 IPCM의 학습/예측 서버 고도화  
- **역할/업무**: Threshold 자동계산 기능 추가, AAKR Sampling 로직 서버화, Version 관리 기능 추가  
- **성과**: Threshold 자동산출 체계 정립, 데이터 전처리 일관성 확보, Version 관리 도입으로 유연성 강화  
- **기술 스택**: Python, InfluxDB, Redis, Kafka, PostgreSQL, Pydantic  

---

## 추가 역량 및 활동
- 시계열 모델(AAKR, ARIMA, VAE, ANNOY, ICA) 교육자료 제작 및 사내 공유  
- 모델 그룹핑, 학습, 최적화 및 알람 관리 프로세스 표준화  
- 도메인 기반 이상 신호 분석 및 문서화 → 현업 이해도 향상 지원  
