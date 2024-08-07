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
    'Fastapi_port' : 1111
}


#모델 정보
MODEL_CONFIG = {
    'test_model': {
        'window_size': 5,
        'step_size': 5
    },
    'real_model': {
        'window_size': 100,
        'step_size': 50
    }
}
