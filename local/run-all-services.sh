

for service_json_spec in `ls things_api/services/*_service.json`; do
  ./run-service.py --spec $service_json_spec &
done

./run-target.py --spec things_api/services/target.json &

wait