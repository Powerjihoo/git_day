# model2.py

from datetime import datetime

from statsmodels.tsa.arima.model import ARIMA

import config
from influx import InfluxConnector

server_info = config.SERVER_CONFIG
model_info = config.MODEL_CONFIG['test_model']

def convert_to_iso_format(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

class ARIMAForecastModel:
    def __init__(self, tagname: str, start_date: str, end_date: str, step_size: int= model_info['window_size']):
        self.tagname = tagname
        self.start_date = convert_to_iso_format(start_date)
        self.end_date = convert_to_iso_format(end_date)
        self.step_size = step_size
        self.influx_connector = InfluxConnector(
            url=server_info['Influx_host'],
            token=server_info['Influx_token'],
            org=server_info['Influx_org'],
            bucket=server_info['Influx_bucket']
        )

    def fetch_data(self):
        print(f"Fetching data for {self.tagname} from {self.start_date} to {self.end_date}...")
        df = self.influx_connector.load_from_influx(
            tagnames=[self.tagname], 
            start=self.start_date, 
            end=self.end_date,
            desired_len = self.step_size
        )
        if df.empty:
            print("No historical data available.")
            return None
        return df['_value'].values

    def predict(self):
        data = self.fetch_data()
        model = ARIMA(data, order=(1, 2, 1)).fit()
        forecast = model.forecast(steps=self.step_size)
        return forecast.tolist()
