import os
import subprocess

def convert_hwp_files_in_folder(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.hwp'):
            hwp_path = os.path.join(folder_path, file_name)
            html_path = os.path.splitext(hwp_path)[0]
            command = ['hwp5html', '--output', html_path, hwp_path]
            subprocess.run(command)
            print(f'Converted {file_name} to HTML.')

folder_path = 'data/data_100/100_version_new'  # 데이터 폴더 경로를 여기에 입력하세요
convert_hwp_files_in_folder(folder_path)