# 프로젝트 설명

## forecast모델
- `main.py` 파일 실행
  - 이후 websockt으로 데이터를 전송하면 receive후 결과값을 send
- `config.py`에서 `test_model` 설정값을 변경하십시오.
  - MODEL_CONFIG('test_model')
    window_size = 학습하는 데이터 양(1분간격   10분 : 10, 1시간 : 60)
    start_date = Influx에서 불러오는 과거 시간 -(1s, 1m, 1h, 1d, 1m, 1y)
    step_size = 예측할 데이터(1분간격   10분 : 10, 1시간 : 60)

### 특이사항
- 계산이 불가능한 경우(이전 시간과 5초 이내 차이, `NaN` 값 포함된 경우), `[None, None]`으로 결과가 전송됩니다.


## trend모델
- 'main.py' 파일 실행
  - 이후 api명령어를 입력하면 결과값 출력
- `config.py`에서 `test_model` 설정값을 변경하십시오.
  - MODEL_CONFIG('test_model')
    duration_size = 예측할 데이터(5초간격   10분 : 120, 1시간 : 720)

## 환경 정보
- Conda 23.1.0
- Python 3.11.0
- 다른 패키지 정보는 `requirements.txt` 파일에서 확인 가능합니다.
  ```bash
  pip install -r requirements.txt


### 사용명령어
- /duration 엔드포인트 사용
  curl -X POST "http://127.0.0.1:1113/duration" -H "Content-Type: application/json" -d "{\"tagname\": 2, \"start\": \"2024-09-13 09:00:00\", \"end\": \"2024-09-13 10:25:00\"}"

- web사용
  {
  "tagname": 2,
  "start": "2024-09-13 09:00:00",
  "end": "2024-09-13 11:00:00"}