#!/bin/sh

APT_SERVER_IP_NAME="pi@sim7600server.local"

cd /home/pi/startup

echo -e "-----> Try connect to ${APT_SERVER_IP_NAME} <-----"
a=0
while ! curl http://${APT_SERVER_IP_NAME}:8000/apt-repo/keys/pgp-key.public > pgp-key.public; do
    echo Trying to connect $a time
    a=`expr $a + 1`
    sleep 1
    
    if [ $a -gt 5 ]
    then
    break
    fi
done

APT_SERVER_IP=$(sshpass -p raspberry ssh -o StrictHostKeyChecking=no ${APT_SERVER_IP_NAME} hostname -I | sed 's/.$//'):8000
echo -e "-----> Sim7600 Server IP = ${APT_SERVER_IP} <-----"

echo -e "-----> Getting Time From ${APT_SERVER_IP} <-----"
sudo date +%Y%m%d%T -s "`sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@sim7600server.local 'date "+%Y%m%d %T"'`"
date

echo -e "-----> Add ${APT_SERVER_IP} to apt sources <-----"
echo "deb [arch=all signed-by=/home/pi/startup/pgp-key.public] http://${APT_SERVER_IP}/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/sim7600prg.list

echo -e "-----> Get sim7600prg by apt <-----"
sudo apt-get clean
sudo apt-get update
sudo apt-get upgrade -y

echo -e "-----> Get System <-----"
sudo sshpass -p raspberry rsync --progress -vratlz --delete -e ssh ${APT_SERVER_IP_NAME}:/home/pi/apt-repo/system/ /home/pi/FlashData

adb start-server

echo -e "-----> Start Sim7600Prg <-----"

sim7600prg
