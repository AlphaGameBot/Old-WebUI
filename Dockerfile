FROM python:3.11.9

WORKDIR /docker

COPY . /docker/


RUN pip install -r /docker/requirements.txt

EXPOSE 5000


CMD ["python", "/docker/src/main.py"]