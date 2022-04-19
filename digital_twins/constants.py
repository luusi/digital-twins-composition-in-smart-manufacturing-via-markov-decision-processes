import websockets

ACCESS_BOSCH_IOT_URL = "https://access.bosch-iot-suite.com"
HEADERS = {
    'accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
}
WS_URI = "wss://things.eu-1.bosch-iot-suite.com/ws/2"
DEFAULT_DEGRADATION_COST = 1.0
DEFAULT_DEGRADATION_PROBABILITY = 0.05
DEFAULT_MAX_BROKEN_PROB = 0.95
