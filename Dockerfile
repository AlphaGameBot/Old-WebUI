FROM python:3.11.9

WORKDIR /docker

COPY . /docker/


RUN pip install -r /docker/requirements.txt

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "python /docker/src/docker/healthcheck.py" ]
CMD ["python", "/docker/src/main.py"]