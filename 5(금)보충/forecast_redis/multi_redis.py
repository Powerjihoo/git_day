import json
import time

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import redis

# Redis 연결
redis_client = redis.Redis(host='localhost', port=6379, db=0)
# redis_client = redis.Redis(host='192.168.110.11', port=6379, db=0)

def check_redis_data(tagname):
    recent_values_key = f"{tagname}:recent_values"
    forecast_key = f"{tagname}:forecast"
    statistics_key = f"{tagname}:statistics" 
    timestamps_key = f"{tagname}:recent_timestamps"  # timestamps 키 추가

    recent_values = redis_client.get(recent_values_key)
    forecast = redis_client.get(forecast_key)
    statistics = redis_client.get(statistics_key)
    timestamps = redis_client.get(timestamps_key)  # timestamps 가져오기

    recent_values = json.loads(recent_values) if recent_values else []
    forecast = json.loads(forecast) if forecast else []
    statistics = json.loads(statistics) if forecast else []
    timestamps = json.loads(timestamps) if timestamps else []  # timestamps 디코딩

    print(f"태그명 : {tagname}")
    print(f"최근 데이터: {recent_values}")
    print(f"예측 데이터: {forecast}")
    print("------------------------------------")
    return recent_values, forecast,  timestamps,statistics  # timestamps도 반환

# 데이터 가져오기 및 시각화
def update_plot(ax, tagname):
    recent_values, forecast,  timestamps,statistics = check_redis_data(tagname)

    # 첫 번째 타임스탬프 값 가져오기
    first_timestamp = pd.to_datetime(timestamps[0])  # 첫 번째 타임스탬프를 datetime 객체로 변환

    # 5초 간격으로 타임스탬프 생성
    recent_timestamps = [first_timestamp + pd.Timedelta(seconds=i * 5) for i in range(len(recent_values))]
    forecast_start_time = recent_timestamps[-1] + pd.Timedelta(seconds=5)  # 최근 타임스탬프 이후 5초 추가
    forecast_timestamps = [forecast_start_time + pd.Timedelta(seconds=i * 5) for i in range(len(forecast))]  # 예측 타임스탬프 생성

    # 데이터프레임 생성
    df_recent = pd.DataFrame({'Temperature': recent_values}, index=recent_timestamps)  # 최근 값의 타임스탬프 설정
    df_forecast = pd.DataFrame({'Forecast': forecast}, index=forecast_timestamps)  # 예측 값의 타임스탬프 설정

    # 그래프 그리기
    ax.clear()  # 이전 그래프 지우기
    ax.plot(df_recent.index, df_recent['Temperature'], label='Recent Values', color='blue')
    ax.plot(df_forecast.index, df_forecast['Forecast'], label='Forecasted Temperature', color='red', linestyle='--')
    ax.fill_between(df_forecast.index, df_forecast['Forecast']-1, df_forecast['Forecast']+1, color='gray', alpha=0.2, label='Forecast ±1°C')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d:%H:%M'))  # 형식 설정
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))  # 1분 간격으로 주요 레이블 표시
    ax.set_title(
    f'Forecast using ARIMA for Tag {tagname}, '
    f'Max: {statistics["max"]:.2f}, Min: {statistics["min"]:.2f}, '
    f'Mean: {statistics["mean"]:.2f}, Variance: {statistics["var"]:.2f}, '
    f'Std Dev: {statistics["std"]:.2f}')
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
