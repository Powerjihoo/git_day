import random  # 랜덤 선택을 위한 모듈 추가
import sys

import numpy as np
import xlwings as xw

print('start')

# 엑셀 파일 직접 열기
excel_path = r"C:\Users\jhpark\Desktop\arima계산과정.xlsm"  # 경로 확인!
wb = xw.Book(excel_path)  # 엑셀 파일 직접 열기
print(f"엑셀 파일을 열었습니다: {wb.fullname}")
# 원하는 시트 가져오기 (여기서는 인덱스 3번 시트)
sheet = wb.sheets[2]
print(f"워크북: {wb.name}, 시트: {sheet.name}")


# 선형 증가 랜덤 데이터 생성 함수
def generate_linear_data(start, end, length, noise=1):
    x = np.linspace(start, end, length)  # start → end로 선형 증가 or 감소
    noise_values = np.random.uniform(-noise, noise, length)  # 랜덤 노이즈 추가
    data = x + noise_values  # 노이즈 적용
    return data.tolist()

# 패턴있는 데이터 생성
base_pattern = [1.3, 1.1, 3.1, 3.9, 1.2, 1.4, 1.1, 3.5, 4.4, 1.3, 
                1.2, 1.1, 3.6, 4.1, 1.3, 1.4, 1.5, 3.1, 4.9, 1.1]
num_patterns = 5
transformed_patterns = []
for _ in range(num_patterns):
    scale = np.random.uniform(1.5, 3.0)  # 1.5배 ~ 3배 스케일링
    offset = np.random.uniform(0, 5)  # 0 ~ 5 범위에서 오프셋 추가
    noise = np.random.uniform(-0.5, 0.5, len(base_pattern))  # -0.5 ~ 0.5 랜덤 노이즈 추가

    new_pattern = [(x * scale) + offset + n for x, n in zip(base_pattern, noise)]
    transformed_patterns.append(new_pattern)

# 랜덤 워크 데이터 생성
def generate_random_walk(n=20):
    return np.cumsum(np.random.normal(0, 1, n)).tolist()

# 셀 주소를 (행, 열)로 변환하는 함수
def cell_to_rowcol(cell_address):
    """엑셀 주소(A1 등)를 (행, 열) 튜플로 변환"""
    cell = sheet.range(cell_address)
    return cell.row, cell.column

# 엑셀에 데이터 추가하는 함수
def write_data_to_excel(sheet, start_cell, data):
    row, col = cell_to_rowcol(start_cell)
    for i, value in enumerate(data):
        sheet.cells(row + i, col).value = value  # 세로로 추가
    

# 첫 번째 버튼: 데이터1 추가 (B6부터 입력)
def main1():
    data1 = generate_linear_data(1, 20, 20, noise=2)   # 1~20 증가 + 노이즈
    data2 = generate_linear_data(1, 50, 20, noise=5)   # 1~50 증가 + 노이즈
    data3 = generate_linear_data(1, 100, 20, noise=10) # 1~100 증가 + 노이즈

    # 감소하는 데이터 (start가 더 크고, end가 더 작아야 함)
    data4 = generate_linear_data(20, 1, 20, noise=2)   # 20~1 감소 + 노이즈
    data5 = generate_linear_data(50, 1, 20, noise=5)   # 50~1 감소 + 노이즈
    data6 = generate_linear_data(100, 1, 20, noise=10) # 100~1 감소 + 노이즈

    # 랜덤으로 하나의 데이터 선택
    random_data = random.choice([data1, data2, data3, data4, data5, data6])
    write_data_to_excel(sheet, "B6", random_data)
    print("데이터1 입력 완료!")


# 두 번째 버튼: 데이터2 추가 (E6부터 입력)
def main2():
    random_data = random.choice(transformed_patterns)  # 5개 패턴 중 랜덤 선택
    write_data_to_excel(sheet, "K6", random_data)
    print("랜덤 데이터 입력 완료!")

# 3번 버튼: 랜덤 워크 데이터 추가 (N16 & J16)
def main3():
    data3 = generate_random_walk(20)  # 랜덤 워크 데이터 생성
    write_data_to_excel(sheet, "B47", data3)  # N16에 추가
    write_data_to_excel(sheet, "M47", data3)  # J16에도 같은 데이터 추가
    print("랜덤 워크 데이터 N16, J16에 입력 완료!")


# 실행 확인용: 커맨드라인 인수를 통해 호출할 함수를 선택
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "main1":
            main1()
        elif cmd == "main2":
            main2()
        elif cmd == "main3":
            main3()
        else:
            print("알 수 없는 명령어입니다. 사용 가능한 명령어: main1, main2, main3")
    else:
        print("스크립트 실행됨. 특정 함수를 호출해야 합니다! 예: python script.py main3")