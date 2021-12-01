# envoy_logger
A Prometheus target for logging data from a Enphase Envoy

virtualenv -p python3 .venv
. .venv/bin/activate
pip install envoy_reader prometheus_client

docker build -t envoy_logger .
docker run envoy_logger
