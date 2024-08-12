import json
import time

import matplotlib.pyplot as plt
import pandas as pd
import redis

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_redis_data(tagname):
    recent_values_key = f"{tagname}:recent_values"
    forecast_key = f"{tagname}:forecast"
    alarm_key = f"{tagname}:alarm"  # alarm 키 추가

    recent_values = redis_client.get(recent_values_key)
    forecast = redis_client.get(forecast_key)
    alarm = redis_client.get(alarm_key)  # alarm 값 가져오기

    recent_values = json.loads(recent_values) if recent_values else []
    forecast = json.loads(forecast) if forecast else []
    alarm = alarm.decode('utf-8') if alarm else None  # alarm 값을 문자열로 디코딩

    print(f"태그명 : {tagname}")
    print(f"최근 데이터: {recent_values}")
    print(f"예측 데이터: {forecast}")
    print(f"알람 상태: {alarm}")  # 알람 값 출력
    print("------------------------------------")
    return recent_values, forecast, alarm

# 데이터 가져오기 및 시각화
def update_plot(ax, tagname):
    recent_values, forecast, alarm = check_redis_data(tagname)

    if not recent_values or not forecast:
        print(f"태그 {tagname} 데이터가 충분하지 않습니다.")
        return
    
    # 시간 인덱스 생성
    total_length = len(recent_values) + len(forecast)
    date_range = pd.date_range(start='2022-01-01', periods=total_length, freq='H')
    
    # 데이터프레임 생성
    df_recent = pd.DataFrame({'Temperature': recent_values}, index=date_range[:len(recent_values)])
    df_forecast = pd.DataFrame({'Forecast': forecast}, index=date_range[len(recent_values):])

    # 그래프 그리기
    ax.clear()  # 이전 그래프 지우기
    ax.plot(df_recent.index, df_recent['Temperature'], label='Recent Values', color='blue')
    ax.plot(df_forecast.index, df_forecast['Forecast'], label='Forecasted Temperature', color='red', linestyle='--')
    ax.fill_between(df_forecast.index, df_forecast['Forecast']-1, df_forecast['Forecast']+1, color='gray', alpha=0.2, label='Forecast ±1°C')
    ax.set_title(f'Temperature Forecast using ARIMA for Tag {tagname},{alarm}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Temperature (°C)')
    ax.legend()
    ax.grid()

def monitor_redis_data():
    tagnames = [1, 2]  # 감시할 태그명 리스트

    # 서브플롯 설정
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12))  # 두 개의 플롯을 위아래로 배치
    
    while True:
        for i, tagname in enumerate(tagnames):
            update_plot(axes[i], tagname)  # 각 태그에 대해 그래프 업데이트
        plt.tight_layout()  # 레이아웃 조정
        plt.pause(3)  # 3초마다 업데이트

if __name__ == "__main__":
    monitor_redis_data()
