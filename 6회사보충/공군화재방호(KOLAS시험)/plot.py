import warnings

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

#데이터 불러오기
use_data = pd.read_csv('test_data.csv', parse_dates=['_time'], index_col='_time')
plt.figure(figsize=(23, 5))
plt.plot(use_data.index, use_data['_value'], label='test_data', color='orange')
plt.grid()
plt.axhline(300,color='red')
plt.axhline(400,color='red')
plt.show()