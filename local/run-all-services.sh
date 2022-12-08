#!/usr/bin/env bash

MY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


for service_json_spec in `ls ${MY_DIR}/things_api/services/*_service.json`; do
  ${MY_DIR}/run-service.py --spec $service_json_spec &
done

${MY_DIR}/run-target.py --spec ${MY_DIR}/things_api/services/target.json &

wait