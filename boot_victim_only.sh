
cd ../config/


echo "[INFO] Using previous initrd, booting process may take couple minutes"
echo "[INFO] Now Booting neu-5-9"

ssh handong@10.255.0.1 hil node power cycle neu-5-9

echo "[INFO] Use the following command to check if victim is booted"
echo "          ping 192.168.1.9"

