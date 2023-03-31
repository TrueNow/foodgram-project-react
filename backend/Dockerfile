FROM python:3.9

WORKDIR /backend
COPY requirements.txt .
RUN apt update && \
    apt upgrade -y && \
    apt -y install gcc && \
    apt -y install gunicorn && \
    python3 -m pip install --upgrade pip && \
    pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]
