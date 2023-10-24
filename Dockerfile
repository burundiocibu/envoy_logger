FROM python:3

ADD . /envoy_logger

RUN pip install /envoy_logger

CMD ["python", "/envoy_logger/envoy_logger/envoy_logger.py"]
