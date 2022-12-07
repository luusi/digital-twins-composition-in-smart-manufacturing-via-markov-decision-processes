#!/usr/bin/env python3
import logging
from typing import Dict

import connexion

from local.things_api.data import ServiceInstance
from local.things_api.helpers import ServiceId

logging.basicConfig(level=logging.INFO)


class ApiServer:

    SERVICES: Dict[ServiceId, ServiceInstance] = {}

    def get_health(self):
        return "Healthy"

    def get_service(self, service_id: str):
        service_id = ServiceId(service_id)
        if service_id not in self.SERVICES:
            return f'Service with id {service_id} not found', 404
        return self.SERVICES[service_id]


api = ApiServer()

app = connexion.App(__name__)
app.add_api('spec.yml')
# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
application = app.app

if __name__ == '__main__':
    # run our standalone server
    app.run(port=8080, server="flask")
