#!/usr/bin/env python3
import logging
from typing import Dict

import connexion
from connexion import NoContent

from local.things_api.data import ServiceInstance
from local.things_api.helpers import ServiceId


logging.basicConfig(level=logging.INFO)


class ApiServer:

    SERVICES: Dict[ServiceId, ServiceInstance] = {}

    def get_health(self):
        return "Healthy"

    def get_services(self):
        return [service.json for service in self.SERVICES.values()], 200

    def get_service(self, service_id: str):
        logging.info(f"Called 'get_service' with ID: {service_id}")
        service_id = ServiceId(service_id)
        if service_id not in self.SERVICES:
            return f'Service with id {service_id} not found', 404
        return self.SERVICES[service_id].json

    def put_service(self, service_id: str, body: Dict):
        logging.info(f"Called 'put_service' with input: {service_id}, {body}")
        service_id = ServiceId(service_id)
        exists = service_id in self.SERVICES
        service_instance = ServiceInstance.from_json(body)
        if service_id != service_instance.service_id:
            return f"service_id in body is not equal to path parameter: {service_id} != {service_instance.service_id}", 400
        if exists:
            logging.info('Updating service %s..', service_id)
        else:
            logging.info('Creating service %s...', service_id)
        self.SERVICES[service_id] = service_instance
        return NoContent, (200 if exists else 201)

    def delete_service(self, service_id: str):
        logging.info(f"Called 'delete_service' with input: {service_id}")
        service_id = ServiceId(service_id)
        if service_id in self.SERVICES:
            logging.info('Deleting service %s...', service_id)
            self.SERVICES.pop(service_id)
            return NoContent, 204
        else:
            return NoContent, 404


api = ApiServer()

app = connexion.App(__name__)
app.add_api('spec.yml')
# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
application = app.app

if __name__ == '__main__':
    # run our standalone server
    app.run(port=8080, server="flask")
