#!/bin/bash
# for ops user Centos
sudo pip install pyyaml
sudo pip install redis
echo "y" | sudo yum install python-devel.x86_64
sudo pip install lmdb
sudo pip install --user gevent
sudo pip install kazoo

sudo mkdir -p /data/lmdb/runtime_policy
sudo chown -R www:www /data/lmdb
