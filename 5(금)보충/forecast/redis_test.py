import json
import time
from datetime import datetime

import redis

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_redis_data():
    for tagname in ['tagname3']:  # 감시할 태그명 리스트
        recent_values_key = f"{tagname}:recent_values"
        forecast_key = f"{tagname}:forecast"
        timestamps_key = f"{tagname}:recent_timestamps"

        recent_values = redis_client.get(recent_values_key)
        forecast = redis_client.get(forecast_key)
        recent_timestamps = redis_client.get(timestamps_key)
        
        recent_values = json.loads(recent_values)
        forecast = json.loads(forecast)
        recent_timestamps = json.loads(recent_timestamps)
        # recent_timestamps = [ts if ts == 'nan' else datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').strftime('%y-%m-%d %H:%M:%S') for ts in recent_timestamps]

        print(f"태그명 : {tagname}")
        print(f"time   : {recent_timestamps}")
        print(f"최근 데이터: {recent_values}")
        print(f"예측 데이터: {forecast}")
        print("------------------------------------")


def monitor_redis_data():
    check_redis_data()
    time.sleep(5)  # 5초마다 확인

if __name__ == "__main__":
    monitor_redis_data()
