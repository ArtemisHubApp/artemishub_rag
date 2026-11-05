FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential curl && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "-m", "pytest"]
