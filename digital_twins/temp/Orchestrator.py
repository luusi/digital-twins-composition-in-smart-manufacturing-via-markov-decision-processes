import asyncio
import websockets
import base64
import time
import requests
import json
import config
import Translator
import subprocess
from ThingsAPI import *
from BuildPDDL import *


async def executionEngine():
    print("Opening websocket endpoint...")
    uri = "wss://things.eu-1.bosch-iot-suite.com/ws/2"
    async with websockets.connect(uri,
                                  extra_headers=websockets.http.Headers({
                                      'Authorization': 'Bearer ' + getToken()
                                  })) as websocket:
        print("Collecting problem data...")
        desc = buildPDDL()
        # Call planner
        # If plan not found, return 2
        print("Invoking planner...")
        command = "./fast-downward.py " + config.PDDL["domainFile"] + " " + config.PDDL[
            "problemFile"] + " " + "--search " + '"astar(lmcut())"'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
        # print(result.returncode)
        if (result.returncode > 9):
            return 2
        print("Plan found! Proceeding to orchestrate devices...")
        with open(config.PDDL["planFile"]) as file_in:
            for line in file_in:
                if line[0] == ";":
                    break
                tokens = line.replace("(", "").replace(")", "").strip().split(" ")
                thingId = config.ThingsAPI["namespace"] + ":" + tokens[1]
                cmd = tokens[0]
                params = []
                for i in range(2, len(tokens)):
                    params.append(tokens[i])

                eventCmd = "START-SEND-EVENTS?filter="
                eventCmd += '(eq(thingId,"' + thingId + \
                            '")'
                print("EVENT_CMD: ", eventCmd)
                eventCmd = urllib.parse.quote(eventCmd,
                                              safe='')

                await websocket.send(eventCmd)
                await websocket.recv()
                print("Listening to events originating from " + thingId)

                expected = desc.getGroundedEffect(cmd, params)
                print("Issuing command " + tokens[0] +
                      " to " + thingId + " with parameters " +
                      str(params))

                print("Expected result: " + str(expected))
                sendMessage(thingId, cmd, json.dumps(params), 0)

                output = None
                while True:
                    try:
                        event = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    except asyncio.TimeoutError:
                        print("Expired timer! Adapting...")
                        return 1
                    print("Received event: ", event)
                    event = json.loads(event)
                    value = event["value"]
                    path = event["path"]
                    if value == "terminated":
                        break
                    if "output" in path:
                        output = value
                print("Received output: " + str(output))
                await websocket.send("STOP-SEND-EVENTS")
                await websocket.recv()
                if output != expected:
                    print("Discrepancy detected! Adapting...")
                    return 1
        return 0


result = asyncio.get_event_loop().run_until_complete(executionEngine())
while result == 1:
    result = asyncio.get_event_loop().run_until_complete(executionEngine())

if result == 0:
    print("Success!")
else:
    print("Plan not found!")

