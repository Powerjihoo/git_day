import json
import time

import matplotlib.pyplot as plt
import redis

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_redis_data(tagname):
    recent_values_key = f"{tagname}:recent_values"
    forecast_key = f"{tagname}:forecast"

    recent_values = redis_client.get(recent_values_key)
    forecast = redis_client.get(forecast_key)
    
    recent_values = json.loads(recent_values) if recent_values else []
    forecast = json.loads(forecast) if forecast else []

    print(f"태그명 : {tagname}")
    print(f"최근 데이터: {recent_values}")
    print(f"예측 데이터: {forecast}")
    print("------------------------------------")
    return recent_values, forecast

# 그래프 설정
plt.ion()  
fig, ax = plt.subplots()
x, y_values, y_forecast = [], [], []

line_values, = ax.plot(x, y_values, 'bo-', label="Recent Values")
line_forecast, = ax.plot(x, y_forecast, 'ro-', label="Forecast")
ax.legend()
ax.set_xlim(0, 5)
ax.set_ylim(0, 10)

def update_plot(recent_values, forecast):
    global x, y_values, y_forecast
    x = list(range(len(recent_values)))

    line_values.set_xdata(x)
    line_values.set_ydata(recent_values)
    line_forecast.set_xdata(x)
    line_forecast.set_ydata(forecast)
    
    ax.relim()  
    ax.autoscale_view()  
    plt.draw()
    plt.pause(1)  

def monitor_redis_data():
    tagname = 1  # 감시할 태그명
    while True:
        recent_values, forecast = check_redis_data(tagname)
        if recent_values and forecast:
            update_plot(recent_values, forecast)
        time.sleep(5)  # 5초마다 확인

if __name__ == "__main__":
    monitor_redis_data()
