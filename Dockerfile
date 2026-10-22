FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY spanish_local_holidays_calendar ./spanish_local_holidays_calendar
COPY tests ./tests

CMD ["python", "-m", "spanish_local_holidays_calendar"]
