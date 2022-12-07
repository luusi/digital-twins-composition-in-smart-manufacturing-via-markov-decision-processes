#!/usr/bin/env python3
import logging

import connexion

logging.basicConfig(level=logging.INFO)


class ApiServer:

    def get_health(self):
        return "Healthy"


api = ApiServer()

app = connexion.App(__name__)
app.add_api('spec.yml')
# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
application = app.app

if __name__ == '__main__':
    # run our standalone server
    app.run(port=8080, server="flask")
