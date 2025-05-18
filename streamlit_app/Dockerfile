FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# 엑셀 파일 처리를 위한 추가 패키지 설치
RUN apt-get update && \
    apt-get install -y curl build-essential libssl-dev libjpeg-dev zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 필요한 Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit openpyxl pandas xlrd

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# PATH 문제를 피하기 위해 python -m streamlit 사용
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]