import requests
import time
import json
import urllib.parse
import config


def getToken():
    clientId = config.ThingsAPI["clientId"]
    clientSecret = config.ThingsAPI["clientSecret"]
    scope = config.ThingsAPI["scope"]


    headers = {
        'accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    payload = {
        'grant_type': 'client_credentials',
        'client_id': clientId,
        'client_secret': clientSecret,
        'scope': scope
    }

    response = requests.post('https://access.bosch-iot-suite.com/token', headers=headers, data=payload)
    # print(response.content)
    token = json.loads(response.content)["access_token"]
    return token


def getThing(thingId):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + getToken(),
    }

    params = (
        ('ids', thingId),
    )

    response = requests.get('https://things.eu-1.bosch-iot-suite.com/api/2/things', headers=headers, params=params)

    return json.loads(response.content)


def getFeature(thingId, featureId, propertyPath):
    headers = {
        'accept': '*/*',
        'Authorization': 'Bearer' + getToken(),
    }

    thingId = urllib.parse.quote(thingId, safe='')
    propertyPath = urllib.parse.quote(propertyPath, safe='')

    response = requests.get(
        'https://things.eu-1.bosch-iot-suite.com/api/2/things/' + thingId + "/features/" + featureId + "/properties/" + propertyPath,
        headers=headers)

    return json.loads(response.content)


def sendMessageToFeature(thingId, featureId, messageSubject, body, timeout):
    headers = {
        'accept': '*/*',
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json',
    }

    params = (
        ('timeout', str(timeout)),
    )

    thingId = urllib.parse.quote(thingId, safe='')

    response = requests.post(
        'https://things.eu-1.bosch-iot-suite.com/api/2/things/' + thingId + "/features/" + featureId + "/inbox/messages/" + messageSubject,
        headers=headers, params=params, data=body)

    return json.loads(response)


def searchThingsWithField(namespace, field):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer' + getToken(),
    }

    params = (
        ('namespaces', namespace),
        ('fields', field),
    )

    response = requests.get('https://things.eu-1.bosch-iot-suite.com/api/2/search/things', headers=headers,
                            params=params)

    return json.loads(response.content)["items"]


def searchThings(namespace):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer' + getToken(),
    }

    response = requests.get('https://things.eu-1.bosch-iot-suite.com/api/2/search/things', headers=headers)

    return json.loads(response.content)["items"]


def sendMessage(thingId, messageSubject, body, timeout):
    headers = {
        'accept': '*/*',
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json',
    }

    params = (
        ('timeout', str(timeout)),
    )

    thingId = urllib.parse.quote(thingId, safe='')
    response = requests.post('https://things.eu-1.bosch-iot-suite.com/api/2/things/' + thingId
                             + '/inbox/messages/' + messageSubject, headers=headers, params=params, data=body)

    return (response)


def changeProperty(thingId, featureId, propertyPath, body):
    headers = {
        'accept': '*/*',
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json',
    }

    data = body
    thingId = urllib.parse.quote(thingId, safe='')
    propertyPath = urllib.parse.quote(propertyPath, safe='')
    response = requests.put('https://things.eu-1.bosch-iot-suite.com/api/2/things/' +
                            thingId +
                            '/features/' + featureId + '/properties/' + propertyPath,
                            headers=headers, data=data)

    return response


print(changeProperty("com.bosch.services:door_device", "status", "value", json.dumps("error")))
# print(searchThings("com.myThings"))
# print(getToken())




