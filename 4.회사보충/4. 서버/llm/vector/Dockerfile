FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu20.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.8 python3-pip python3.8-distutils nvidia-docker2

RUN python3.8 -m pip install --no-cache-dir --upgrade pip setuptools

COPY requirements.txt /app/requirements.txt
RUN chmod +x entrypoint.sh
COPY . /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/app/entrypoint.sh"]


