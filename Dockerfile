FROM python:3

ADD envoy_logger/envoy_logger.py /

RUN pip install envoy_reader prometheus_client

CMD ["python", "./envoy_logger.py"]
