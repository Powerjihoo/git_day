FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-devel

WORKDIR /app
COPY ./src /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 별도의 run.sh 실행권한 부여 및 ENTRYPOINT 설정
RUN chmod +x /app/run.sh
ENTRYPOINT ["/app/run.sh"]
