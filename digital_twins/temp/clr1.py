import netifaces
import paho.mqtt.client as mqtt
import datetime, threading, time
import json

# DEVICE CONFIG GOES HERE
tenantId = "t721ea604314e493aa54719bf70128483_hub"
device_password = "boschthings"
hub_adapter_host = "mqtt.bosch-iot-hub.com"
deviceId = "com.myThings:clr1"
clientId = deviceId
authId = "com.myThings_clr1"
certificatePath = "./iothub.crt"
ditto_topic = "com.myThings/clr1"


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print("Connection to MQTT broker failed: " + str(rc))
        return

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # BEGIN SAMPLE CODE
    client.subscribe("command///req/#")
    # END SAMPLE CODE
    print("Connected")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Command received...")
    cmd = json.loads(msg.payload.decode("utf-8"))
    cmdName = cmd["topic"].split("/")[-1]
    params = cmd["value"]
    changeStatus(json.dumps("busy"))
    executeCommand(cmdName, params)
    changeStatus(json.dumps("terminated"))


def executeCommand(name, params):
    if name == "cool":
        added = []
        deleted = []
        added.append(params[0] + ".cooled:" + "true")
        deleted.append(params[0] + ".cooled:" + "false")
        output = dict(added=added, deleted=deleted)

        publishOutput(json.dumps(output))


def updateState(feature, value):
    payload = '{"topic": "' + ditto_topic + \
              '/things/twin/commands/modify","headers": {"response-required": false},' + \
              '"path": "/features/' + feature + '/properties/value/current","value" : ' + value + '}'
    client.publish(publishTopic, payload)


def publishOutput(output):
    payload = '{"topic": "' + ditto_topic + \
              '/things/twin/commands/modify","headers": {"response-required": false},' + \
              '"path": "/features/output/properties/value","value" : ' + output + '}'
    client.publish(publishTopic, payload)


def changeStatus(status):
    payload = '{"topic": "' + ditto_topic + \
              '/things/twin/commands/modify","headers": {"response-required": false},' + \
              '"path": "/features/status/properties/value","value" : ' + status + '}'
    client.publish(publishTopic, payload)


# Period for publishing data to the MQTT broker in seconds
timePeriod = 10

# Configuration of client ID and publish topic
publishTopic = "telemetry/" + tenantId + "/" + deviceId

# Output relevant information for consumers of our information
print("Connecting client:    ", clientId)
print("Publishing to topic:  ", publishTopic)

# Create the MQTT client
client = mqtt.Client(clientId)
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(certificatePath)
username = authId + "@" + tenantId
client.username_pw_set(username, device_password)
client.connect(hub_adapter_host, 8883, 60)

client.loop_start()

while (1):
    pass