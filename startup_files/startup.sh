#!/bin/sh

APT_SERVER_IP="192.168.88.10:8000"

cd /home/pi/startup

echo -e "\n--- Get sim7600prg ---\n"
a=0
while ! curl http://${APT_SERVER_IP}/apt-repo/keys/pgp-key.public > pgp-key.public; do
    echo Trying to connect $a time
    a=`expr $a + 1`
    sleep 1
    
    if [ $a -gt 30 ]
    then
    break
    fi
done

echo "deb [arch=all signed-by=/home/pi/startup/pgp-key.public] http://${APT_SERVER_IP}/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/sim7600prg.list

sudo systemctl restart systemd-timesyncd.service

a=0
while [[ "$(sudo timedatectl | grep synchronized)" != \
         "System clock synchronized: yes" ]]; do

    echo Trying to sync data $a time
    a=`expr $a + 1`
    sleep 1
    
    if [ $a -gt 10 ]
    then
    break
    fi

done

echo -e "\n--- Time Synced--- \n"

sudo apt clean
sudo apt update
sudo apt upgrade sim7600prg -y

echo -e "\n--- Get System ---\n"

file1="/home/pi/startup/SysRelease"
file2="/home/pi/startup/NewSysRelease"

if curl http://${APT_SERVER_IP}/apt-repo/system/Release > NewSysRelease; 
then
    if cmp -s "$file1" "$file2"; then
        echo -e "\n--- No updates ---\n"
    else
        VERSION=$(cat NewSysRelease | grep "Version")
        VERSION=${VERSION:9}
        echo -e "\n--- New version ${VERSION} available ---\n"

        cat NewSysRelease > SysRelease
        rm NewSysRelease

        curl http://${APT_SERVER_IP}/apt-repo/system/sim7600system_${VERSION}.tar.gz > flashdata.tar.gz
        mkdir -p /home/pi/FlashData
        rm /home/pi/FlashData/*
        tar xzfv flashdata.tar.gz -C /home/pi/FlashData/
    fi
fi

adb start-server

echo -e "\n--- Start Sim7600Prg ---\n"

sim7600prg
