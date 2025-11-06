FROM python:3.6-slim

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=9090

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==21.3.1 \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9090

CMD ["python", "app.py"]