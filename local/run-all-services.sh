

for service_json_spec in `ls things_api/services/*`; do
  ./run-service.py --spec $service_json_spec &
done

wait