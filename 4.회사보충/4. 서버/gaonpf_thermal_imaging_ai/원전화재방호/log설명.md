# 로그 설명

## app.py파일
- logger.info(f"Received: tagname = {tag_name}, value={values}, timestamp={timestamp_str}")
  - websocket에서 수신되는 데이터의 정보 확인

- logger.warning(f"Unknown tagname received: {tag_name}")
  - postgreDB에는 없는 tagname이 들어왔을때 알림

- logger.error(f"WebSocket connection error: {str(e)}")
  - Websocket이 연결 안됐을때 알림

- logger.warning(f"No data available for the given range: {start} to {end}")
  - 지정한 start - end 사이에 데이터가 없을때 알림

- logger.warning(f"Unknown tagname received: {tag_name}")
  - postgreDB에는 없는 tagname이 들어왔을때 알림

## model.py파일
- logger.error(f"Error during ARIMA model training and forecasting: {e}")
  - ARIMA모델 실행 시 오류가 발생했을떄 알림

- logger.info(f"Loaded initial data from InfluxDB for tagname = {tag_name}")
  - influxDB에서 데이터를 불러왔을때 확인

- logger.info(f"Prediction successful for tagname = {tag_name}")
  - ARIMA모델 실행까지 완료됐을때 알림

- logger.warning(f"tagname = {tag_name} - Filled count is {filled_count}. Not enough data to forecast.")
  - 충분한 데이터가 없었을때 알림 (config.py의 window_size만큼의 데이터가 쌓이지 않았을때)

- logger.warning(f"tagname = {tag_name} - Update ignored (time difference <= 5 seconds)")
  - Websocket에서 들어와 업데이트 되는 데이터가 이전데이터와 5초이하의 차이가 날때