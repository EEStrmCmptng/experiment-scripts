../dependencies/flink-simplified/build-target/bin/flink run ../dependencies/flink-benchmarks/target/kinesisBenchmarkMoc-1.1-SNAPSHOT-jar-with-dependencies.jar --ratelist $1_600000 --buffer-Timeout 20
echo "[INFO] Flink workloads has finished"
