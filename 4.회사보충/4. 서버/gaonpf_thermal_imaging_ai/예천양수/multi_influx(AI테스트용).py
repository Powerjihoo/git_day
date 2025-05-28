# AI테스트용

import random
import time

from influxdb_client import InfluxDBClient, Point

# InfluxDB 연결 설정
url = "http://localhost:8086"
token = "TwrNN4J0ablMZFPFRB9GsUahs-uESVsM6WU0KKtY-jvJrFbhnxt7atnPg2wyU801B2GbFprJtomq5N1jog9uAg=="
org = "gaonpf"
bucket = "thermal_data"

# InfluxDB 클라이언트 생성
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# 1초마다 데이터를 InfluxDB에 기록하는 함수
def write_data():
    tag_prefixes = ['1', '2','3','4']
    count = 0
    
    while True:
        tag_value = tag_prefixes[count%4]  # tagName이 1 또는 2로 시작하는 값을 번갈아 선택
        point = Point("rawvalue") \
            .tag("tagName", tag_value) \
            .field("_value", round(random.uniform(36, 38), 2))  # 데이터를 "_value" 필드로 설정
        
        write_api.write(bucket=bucket, org=org, record=point)
        print(f"Written point: {point}")
        
        count += 1
        time.sleep(1)  # 1초 대기

try:
    write_data()
except KeyboardInterrupt:
    print("Stopped writing data")
finally:
    client.close()
