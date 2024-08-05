# - Artificial Intelligence Leak Detection Server
인공지능 기반 누수탐사 시스템 Server

## Features
```bash
- 누수타입 분류
    1 .신규 FFT 데이터 입력시 전처리과정을 거치고 4개의 모델통과
    2. 누수여부를 분류해 (0:누수아님, 1:누수)로 출력

- 거리예측
    1. 신규 FFT 데이터 중 누수타입 분류과정에서 누수로 분류된 데이터만 분리
    2. 가까운 거리를 가지는 데이터의 특징을 이용해 거리 예측
    3. 최종적으로 (not_leak : 누수아님, True : 근거리누수, False : 장거리누수)로 출력
```

## API Documentation
```bash
- Swagger: http://{host}/{port}/docs
- Redoc: http://{host}/{port}/redoc
```
## Build Process
```bash
pip list --format=freeze > ./requirements.txt
pyinstaller main.spec --noconfirm
```


## Implemetation
### Window
**서비스 등록**
```bash
- Command Prompt
- nssm.exe install "GaonPlatform Artificial Intelligence Leak Detection Server"
```

**서비스 실행**
```bash
- service.msc
- GaonPlatform Artificial Intelligence Leak Detection Server 서비스 실행 / 중지
```

**설정**
```bash
- dev(192.168.180.200)
    [databases.NaturalDisasterDB]
    host = "192.168.180.200"
    port = 5433
    database = "ngad"
    username = "postgres"
    password = "gp0308@@@"

- demo(192.168.1.2)
    [databases.NaturalDisasterDB]
    host = "192.168.1.2"
    port = 55432
    database = "ngad"
    username = "postgres"
    password = "gp0308@@@"
- 현장(10.151.3.37)
    [databases.NaturalDisasterDB]
    host = "10.151.3.37"
    port = 55432
    database = "ngad"
    username = "postgres"???
    password = "gp0308@@@"???
- 모델설명 ('model/')
    1. classifier_model1.pkl : 고주파대역 분류모델
    2. classifier_model2.pkl : 조화성분 분류모델 
    3. classifier_model3.pkl : 파동성분 분류모델 
    4. classifier_model4.pkl : 1X대역기준 분류모델
    ```