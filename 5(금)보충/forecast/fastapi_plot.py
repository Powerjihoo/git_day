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
    
    return recent_values, forecast

# 그래프 설정
plt.ion()  # Interactive mode on
fig, ax = plt.subplots()
x, y_values, y_forecast = [], [], []

# Initial plot for recent values
line_values, = ax.plot(x, y_values, 'bo-', label="Recent Values")
# Initial plot for forecast
line_forecast, = ax.plot(x, y_forecast, 'ro-', label="Forecast")
ax.legend()
ax.set_xlim(0, 10)
ax.set_ylim(0, 1)

# Function to update plot
def update_plot(recent_values, forecast):
    global x, y_values, y_forecast
    
    if len(recent_values) < 10:
        x = list(range(len(recent_values)))
    else:
        x = list(range(10))
    
    y_values = recent_values[-10:]
    y_forecast = forecast[-10:]

    line_values.set_xdata(x)
    line_values.set_ydata(y_values)
    line_forecast.set_xdata(x)
    line_forecast.set_ydata(y_forecast)
    
    ax.relim()  # Recompute limits
    ax.autoscale_view()  # Autoscale
    plt.draw()
    plt.pause(1)  # Pause for 1 second

def monitor_redis_data():
    tagname = 'tagname3'  # 감시할 태그명
    while True:
        recent_values, forecast = check_redis_data(tagname)
        if recent_values and forecast:
            update_plot(recent_values, forecast)
        time.sleep(5)  # 5초마다 확인

if __name__ == "__main__":
    monitor_redis_data()
