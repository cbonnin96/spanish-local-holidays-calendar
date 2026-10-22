FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY tests ./tests

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "spanish_local_holidays_calendar"]
