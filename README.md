# envoy_logger
A Prometheus target for logging data from a Enphase Envoy

virtualenv -p python3 .venv
. .venv/bin/activate
pip install  prometheus_client requests
pip install -e .

docker build -t envoy_logger .

docker run -e user=$enphase_user -e password=$enphase_password -e serial=$envoy_serial -e hostname=envoy.groot-iot envoy_logger

# Token Base auth
https://enphase.com/download/accessing-iq-gateway-local-apis-or-local-ui-token-based-authentication

