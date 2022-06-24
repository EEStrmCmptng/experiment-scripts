echo "[INFO] Launching the flink workloads"

../dependencies/flink/bin/stop-cluster.sh
../dependencies/flink/bin/start-cluster.sh
../dependencies/flink/bin/flink run /home/like/eestreaming/dependencies/cloud-provider-benchmarks/general/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist 1000_300000 --buffer-Timeout 20


echo "[INFO] Flink workloads has finished"


