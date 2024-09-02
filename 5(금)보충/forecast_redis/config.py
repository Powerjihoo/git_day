#config파일
#redis, postgre, fastapi서버정보
SERVER_CONFIG = {
    'redis_host' : 'localhost',
    'redis_port' : 6379,
    'redis_db' :0,


    'postgre_host' : '192.168.110.11',
    'postgre_port' : 15432,
    'postgre_dbname' : 'thermal_imaging',
    'postgre_user' : 'gaonpf',
    'postgre_pw' : 'gaonpf',


    'Fastapi_host' : 'localhost',
    'Fastapi_port' : 1113,


    # 'Influx_host' : "http://192.168.10.60:8086",
    # 'Influx_token' : "tzxpkRANOkRZsCxEDEDyxKHNFTzt6pIQYJcJY5o_9wCM0QNaTfxuKWstSYMzZnCe7lBTv0Ai7flewVI4CuqILA==",
    # 'Influx_org' : "gaonpf",
    # 'Influx_bucket' : "thermal_data",

    #jihoo
    'Influx_host' : "http://localhost:8086",    
    'Influx_token' : "TwrNN4J0ablMZFPFRB9GsUahs-uESVsM6WU0KKtY-jvJrFbhnxt7atnPg2wyU801B2GbFprJtomq5N1jog9uAg==",
    'Influx_org' : "gaonpf",
    'Influx_bucket' : "thermal_data",
}


#모델 정보
MODEL_CONFIG = {
    'test_model': {
        'window_size': 5, #10분
        'step_size'  : 5,    #10분
        'start_date' : "-10m"
    },
    'real_model': {
        'window_size': 720,    #1시간
        'step_size'  : 720,    #1시간
        'start_date' : "-1h"
    }
}


duration_config = {
    ''
}