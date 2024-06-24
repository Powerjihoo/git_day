# redis.py
import json
import time
from datetime import datetime

import redis

# Redis 클라이언트 초기화
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_redis_data():
    for tagname in ['TagName1', 'TagName2', 'TagName3']:  # 감시할 태그명 리스트
        recent_values_key = f"{tagname}:recent_values"
        recent_values = redis_client.get(recent_values_key)

        if recent_values:
            recent_values = json.loads(recent_values)
            forecast_key = f"{tagname}:forecast"
            forecast = redis_client.get(forecast_key)
            if forecast:
                forecast = json.loads(forecast)
            else:
                forecast = "예측 불가"

            print(f"태그명: {tagname}")
            print(f"최근 데이터: {recent_values}")
            print(f"예측값: {forecast}")
            print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("------------------------------------")

def monitor_redis_data():
    while True:
        check_redis_data()
        time.sleep(5)  # 5초마다 확인

if __name__ == "__main__":
    monitor_redis_data()
