# Setting up and using Rclone

1. on your OWN computer install rclone using curl
```
sudo -v ; curl https://rclone.org/install.sh | sudo bash
```
2. Start configuring
```
rclone config
```
3. Configuration options
```
n
eestreaming
18
<blank>
<blank>
1
<blank>
n
n
```
4. In a terminal on a machine with a web browser, type:
```
rclone authorize "drive" "<key from server>"
```
5. This will give you a code to paste in the server
6. Continue with configuration
```
y
```
7. Enter the number corresponding to the EEstreaming shared drive
8. Continue
```
y
q

```
9. To set it up on a cloudlab instance, redo step 1 on cloudlab and then use the following command on your OWN computer:
```
scp  ~/.config/rclone/rclone.conf <cloudlab server>:~/.config/rclone/rclone.conf
```

10. To send to google drive:
```
rclone copy Desktop/cleanup.txt eestreaming:test
```
11. To send to physical drive:
```
rclone sync --interactive <source> <destination>
```
on linux the drive sould be under /media
