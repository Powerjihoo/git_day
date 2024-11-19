import time
import warnings

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

#데이터 불러오기
use_data = pd.read_csv('sim/use_data.csv', parse_dates=['_time'], index_col='_time')

results = []
test_count = 0
time_start = time.time()

# 슬라이딩 예측 수행 (전체 데이터에서 1분 간격으로 학습 시작 시간 설정)
start_time = use_data.index.min()

# end_time을 데이터의 마지막 시간 1분 전으로 설정
end_time = use_data.index[-1] - pd.Timedelta(minutes=1)

# start_time부터 end_time까지 1분씩 증가하면서 슬라이딩
while start_time + pd.Timedelta(hours=1) <= end_time:
    train_end = start_time + pd.Timedelta(hours=1)  # 학습 시간 구간 설정 (1시간)
    
    # 1시간 간격 데이터 추출
    train_window = use_data.loc[start_time:train_end]  
    
    # ARIMA 모델 학습
    model = ARIMA(train_window, order=(12, 2, 6))
    model_fit = model.fit()

    # 30분 예측
    forecast = model_fit.forecast(steps=30)
    forecast_df = pd.DataFrame(forecast)
    forecast_transpose = forecast_df.T
    forecast_transpose.index = [forecast_transpose.columns[0]]
    forecast_transpose.columns = [f'{i}min_later' for i in range(1, len(forecast_transpose.columns) + 1)]
    forecast_transpose['pred_max'] = forecast_transpose.iloc[0].max()
    forecast_transpose['alarm'] = (forecast_transpose.iloc[0] > 65).any()
    results.append(forecast_transpose)
    test_count+=1
    print(f'{test_count}번째 테스트 완료')
    # 1분 간격으로 학습 시작 시간 이동
    start_time += pd.Timedelta(minutes=1)

# 결과를 하나의 데이터프레임으로 합치기
results_df = pd.concat(results)

# final_alarm 열 생성 및 alarm 기준 설정
results_df['final_alarm'] = False
results_df['consecutive_alarm'] = results_df['alarm'].rolling(window=5).apply(lambda x: all(x), raw=True)
results_df['final_alarm'] = results_df['consecutive_alarm'] >= 1
results_df.drop(columns='consecutive_alarm', inplace=True)

## 결과물 생성 및 병합
use_data_A = use_data.copy()


##정답지 만들기
#실제 값에서부터 30분 미래까지의 최대값 확인
use_data_A['real_max'] = use_data_A['_value'][::-1].rolling(window=30, min_periods=1).max()[::-1]
use_data_A.fillna(0, inplace=True)

#30분 미래값에서 65를 넘는값이 있다면 비정상으로 확인
use_data_A['abnormal'] = (use_data_A['real_max'] > 65)
use_data_A['abnormal'].fillna(False, inplace=True)

# final_abnormal 열 생성 및 abnormal 기준 설정
use_data_A['final_abnormal'] = False
use_data_A['consecutive_abnormal'] = use_data_A['abnormal'].rolling(window=5).apply(lambda x: all(x), raw=True)
use_data_A['final_abnormal'] = use_data_A['consecutive_abnormal'] >= 1
use_data_A.drop(columns='consecutive_abnormal', inplace=True)



# #30분 미래값, 실제 비정상여부, 알람여부 확인
merged_df = results_df.merge(use_data_A[['real_max', 'abnormal', 'final_abnormal']], left_index=True, right_index=True, how='left')
merged_df['result'] = merged_df['final_abnormal'] == merged_df['final_alarm']
merged_df.to_csv('result/total_result.csv')


# 그래프 그리기
plt.figure(figsize=(23, 8))
plt.plot(use_data.index, use_data['_value'], label='use_data (original data)', color='orange')

# 예측 결과 플로팅
for i, result in enumerate(results):
    forecast_start_time = result.index[0]  # 예측 시작 시간
    forecast_values = result.iloc[0, :-2]  # 예측된 값 (마지막 열은 'alarm'임)
    forecast_index = pd.date_range(start=forecast_start_time, periods=len(forecast_values), freq='T')
    plt.plot(forecast_index, forecast_values, label=f'Forecast {i + 1}', linestyle='-', linewidth=2)

# 플롯 라벨과 제목 설정
plt.xlabel('Time')
plt.ylabel('Forecast Values')
plt.title('ARIMA Forecast Results')
plt.grid()
plt.ylim(0,150)
plt.axhline(65,color='red')
plt.savefig('result/total_result.png')

time_end = time.time()
time_calc = time_end - time_start
print(f"코드 수행시간 : {time_calc/60}분")