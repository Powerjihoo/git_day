#config파일
#redis, postgre, fastapi서버정보
SERVER_CONFIG = {
    'postgre_host' : '192.168.110.11',
    'postgre_port' : 15432,
    'postgre_dbname' : 'thermal_imaging',
    'postgre_user' : 'gaonpf',
    'postgre_pw' : 'gaonpf',


    'Fastapi_host' : 'localhost',
    'Fastapi_port' : 1113,


    'Influx_host' : "http://localhost:8086",    
    'Influx_token' : "TwrNN4J0ablMZFPFRB9GsUahs-uESVsM6WU0KKtY-jvJrFbhnxt7atnPg2wyU801B2GbFprJtomq5N1jog9uAg==",
    'Influx_org' : "gaonpf",
    'Influx_bucket' : "thermal_data",
}


#모델 정보
MODEL_CONFIG = {
    'test_model': {
        #forecast용
        'window_size': 720,
        'step_size'  : 120,    
        'start_date' : "-1h",
        
        #trend용
        'duration_size' : 120
    }
}