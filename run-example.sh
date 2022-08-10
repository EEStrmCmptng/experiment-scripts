RATE="100_60000"
QUERY=1

usage() {                                 # Function: Print a help message.
  echo "Usage: $0 [ -r RATE_LIST ] [ -q QUERY ]" 1>&2
}

exit_abnormal() {                         # Function: Exit with error.
  usage
  exit 1
}


while getopts ":q:r:h:" options; do         # Loop: Get the next option;
                                          # use silent error checking;
                                          # options n and t take arguments.
  case "${options}" in                    #
    r)                                    # If the option is n,
      RATE=${OPTARG}                      # set $NAME to specified value.
      ;;
    q)                                    # If the option is t,
      QUERY=${OPTARG}
      if [[ ! "$QUERY" =~ ^(1|5|7|9)$ ]]; then
      	 echo "Invalid Query"
	 exit_abnormal
      fi
      ;;
    :)                                    # If expected argument omitted:
      echo "Error: -${OPTARG} requires an argument."
      exit_abnormal                       # Exit abnormally.
      ;;
    *)
      echo "No argument"
      exit_abnormal                       # Exit abnormally.
      ;;
  esac
done



echo " "
echo "[INFO] -----------------------------------------------------------"
echo "[INFO] Running the Experiment Example on Query 1 at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO]"

echo "[INFO] ------------------------------------------------------------ "
echo "[INFO] Running the Prebuild Flink workload"
./start-flink.sh
./run_flink_one.sh $RATE

echo "[INFO]"
echo "[INFO] ------------------------------------------------------------ "
echo "[INFO} Run Success~!"
echo "[INFO] The experiment is now finished at $(date +"%r")"
echo "[INFO] ------------------------------------------------------------ "
echo " "
