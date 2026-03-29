FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
        calibre \
        xvfb \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & uvicorn main:app --host 0.0.0.0 --port 8000"]
