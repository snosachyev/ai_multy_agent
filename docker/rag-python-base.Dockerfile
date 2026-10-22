FROM transformer-base:latest

WORKDIR /app

COPY ./docker/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade --no-cache-dir -r /tmp/requirements.txt