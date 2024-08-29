import random
import time

from influxdb_client import InfluxDBClient, Point, WritePrecision

# InfluxDB 연결 설정
url = "http://localhost:8086"  # InfluxDB URL
token = "TwrNN4J0ablMZFPFRB9GsUahs-uESVsM6WU0KKtY-jvJrFbhnxt7atnPg2wyU801B2GbFprJtomq5N1jog9uAg=="
org = "gaonpf"               # InfluxDB 조직 이름
bucket = "thermal_data"     # InfluxDB 버킷 이름

# InfluxDB 클라이언트 생성
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# 1초마다 데이터를 InfluxDB에 기록하는 함수
def write_data():
    tag_prefixes = ['1', '2']
    count = 0
    
    while True:
        tag_value = tag_prefixes[count % 2]  # tagname이 1 또는 2로 시작하는 값을 번갈아 선택
        point = Point("raw_value") \
            .tag("tagname", f"{tag_value}_tag") \
            .field("field_key", random.uniform(36, 38))  # 여기에 기록할 데이터를 설정 (예: 카운터 값)
        
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
