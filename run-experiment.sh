echo " "
echo "[INFO] -----------------------------------------------------------"
echo "[INFO] Running the Experiment on Query $1 at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO]"

if [ $# -eq 0 ]
  then
    echo "[ERROR] Experiment Terminated: No Arguments are provided"
    echo " "
    exit
fi

./prep.sh $1

echo "[INFO] ------------------------------------------------------------ "
echo "[INFO] Running the Flink workload on Query $1 at $(date +"%r")"

./run_flink.sh runFlink

echo "[INFO]"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO} Run Success~!"
echo "[INFO] The experiment is now finished at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo " "
