import warnings

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

#데이터 불러오기
use_data = pd.read_csv('sim/use_data.csv', parse_dates=['_time'], index_col='_time')

plt.figure(figsize=(23, 8))
plt.plot(use_data.index, use_data['_value'], label='use_data (original data)', color='orange')
plt.show()