echo " "
echo "[INFO] -----------------------------------------------------------"
echo "[INFO] Running the Experiment Example on Query 1 at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO]"

echo "[INFO] ------------------------------------------------------------ "
echo "[INFO] Running the Prebuild Flink workload"

./run_flink_one.sh runFlink

echo "[INFO]"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO} Run Success~!"
echo "[INFO] The experiment is now finished at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo " "
