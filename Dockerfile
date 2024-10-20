# Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY stand_in_notifier.py ./

CMD ["python", "stand_in_notifier.py"]
