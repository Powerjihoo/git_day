## config.py
import os

SERVER_CONFIG = {
    # postgre 정보
    # 'postgre_host' : '192.168.110.41',
    'postgre_host' : "db",
    'postgre_port' : 5432,
    'postgre_dbname' : 'thermal_imaging',
    'postgre_user' : 'gaonpf',
    'postgre_pw' : 'gaonpf',

    # influxdb 정보
    # 'Influx_host' : 'http://192.168.110.41:8086',
    # 'Influx_token' : os.getenv('INFLUXDB_TOKEN', 'gaonpf-token'),
    # 'Influx_org' : "gaonpf",
    # 'Influx_bucket' : "thermal_data",


    #jihoo
    'Influx_host' : "http://localhost:8086",    
    'Influx_token' : "TwrNN4J0ablMZFPFRB9GsUahs-uESVsM6WU0KKtY-jvJrFbhnxt7atnPg2wyU801B2GbFprJtomq5N1jog9uAg==",
    'Influx_org' : "gaonpf",
    'Influx_bucket' : "thermal_data",

    # fastapi 정보
    'Fastapi_host' : 'localhost',
    'Fastapi_port' : 1114,
}


#모델 정보#모델 정보
MODEL_CONFIG = {
    'test_model': {
        #forecast용
        'window_size': 60,     #학습할 데이터 개수(1분당 1개단위 60 = 1시간)
        'step_size'  : 30,     #예측할 데이터 개수(1분당 1개단위 30 = 30분)
        'start_date' : "-1h"   #influxdb에서 불러올 데이터의 과거 시점(과거 1시간)
        ,
        #trend용               #trend에서는 특정 기간을 확인하기 때문에 window_size가 없음
        'duration_size' : 30   #예측할 데이터 개수(1분당 1개단위 30 = 30분)
    }
}