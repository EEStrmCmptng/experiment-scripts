## setup


### all nodes
```
curl --proto '=https' --tlsv1.2 -sSf https://tiup-mirrors.pingcap.com/install.sh | sh

sudo mkdir /tidb-deploy
sudo mkdir /tidb-data
sudo chmod 777 /tidb-*
```

### on jobmanager
```
tiup cluster deploy tidb-test v6.5.0 tidbtopo.yaml
tiup cluster start tidb-test --init
```
