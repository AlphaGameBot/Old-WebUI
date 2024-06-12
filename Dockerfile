FROM python:3.13.0b1-slim

WORKDIR /docker

COPY . /docker/


RUN pip install -r /docker/requirements.txt

EXPOSE 5000


CMD ["python", "/docker/src/main.py"]