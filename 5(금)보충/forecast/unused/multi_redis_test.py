import json
import time

import redis

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_redis_data():
    tagnames = ['1', '2', '4']  # 감시할 태그명 리스트 (문자열로 변경)

    for tagname in tagnames:
        recent_values_key = f"{tagname}:recent_values"
        forecast_key = f"{tagname}:forecast"
        timestamps_key = f"{tagname}:recent_timestamps"

        # Redis에서 데이터 가져오기
        recent_values = redis_client.get(recent_values_key)
        forecast = redis_client.get(forecast_key)
        recent_timestamps = redis_client.get(timestamps_key)

        # None 값 처리
        recent_values = json.loads(recent_values) if recent_values else []
        forecast = json.loads(forecast) if forecast else []
        recent_timestamps = json.loads(recent_timestamps) if recent_timestamps else []

        print(f"태그명 : {tagname}")
        print(f"time   : {recent_timestamps}")
        print(f"최근 데이터: {recent_values}")
        print(f"예측 데이터: {forecast}")
        print("------------------------------------")


def monitor_redis_data():
    while True:
        check_redis_data()
        time.sleep(5)  # 5초마다 확인

if __name__ == "__main__":
    monitor_redis_data()
