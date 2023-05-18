#!/bin/sh

APT_SERVER_IP="pi@sim7600server.local:8000"

cd /home/pi/startup

echo -e "\n--- Try connect to ${APT_SERVER_IP} ---"
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

echo -e "\n--- Add ${APT_SERVER_IP} to apt sources ---"
echo "deb [arch=all signed-by=/home/pi/startup/pgp-key.public] http://${APT_SERVER_IP}/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/sim7600prg.list

echo -e "\n--- Getting Time From ${APT_SERVER_IP}---"

dateFromServer=$(curl -v --insecure --silent http://${APT_SERVER_IP} 2>&1 \
       | grep Date | sed -e 's/< Date: //'); date +"%Y%m%d %T" -d "$dateFromServer"   

date +%Y%m%d%T -s "$dateFromServer"

date -u

echo -e "\n--- Get sim7600prg by apt ---"
sudo apt-get clean
sudo apt-get update
sudo apt-get upgrade -y

echo -e "\n--- Get System ---"

file1="/home/pi/startup/SysRelease"
file2="/home/pi/startup/NewSysRelease"

if curl http://${APT_SERVER_IP}/apt-repo/system/Release > NewSysRelease; 
then
    if cmp -s "$file1" "$file2"; then
        echo -e "\n--- No updates ---\n"
        rm NewSysRelease
    else
        VERSION=$(cat NewSysRelease | grep "Version")
        VERSION=${VERSION:9}
        echo -e "\n--- New version ${VERSION} available ---\n"

        curl http://${APT_SERVER_IP}/apt-repo/system/sim7600system_${VERSION}.tar.gz > flashdata.tar.gz
        mkdir -p /home/pi/FlashData
        rm /home/pi/FlashData/*
        tar xzfv flashdata.tar.gz -C /home/pi/FlashData/

        rm flashdata.tar.gz

        cat NewSysRelease > SysRelease
        rm NewSysRelease
    fi
fi

adb start-server

echo -e "\n--- Start Sim7600Prg ---\n"

sim7600prg
