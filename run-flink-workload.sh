
echo "[INFO] Launching the flink workloads"

../dependencies/flink-simplified/build-target/bin/flink run ../dependencies/flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist $1 --buffer-Timeout 20
echo "[INFO] Flink workloads has finished"


