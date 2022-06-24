
cd ../config/

echo "[INFO] Packing initrd, these might takes up to few minutes"
cpio-pack -d flink_initrd -o flink_initrd.cpio
gzip -f9 flink_initrd.cpio
cp flink_initrd.cpio.gz /root/tftpboot/linux/initrd.neu-5-9

echo "[INFO] Initrd for neu-5-9 is ready"
echo "[INFO] Now Booting neu-5-9"

ssh handong@10.255.0.1 hil node power cycle neu-5-9

echo "[INFO] Use the following command to check if victim is booted"
echo "          ping 192.168.1.9"

