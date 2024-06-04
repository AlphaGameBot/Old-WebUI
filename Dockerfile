FROM python:3.11.9

COPY . /docker

WORKDIR /docker

RUN pip install -r requirements.txt

CMD ["python", "main.py"]