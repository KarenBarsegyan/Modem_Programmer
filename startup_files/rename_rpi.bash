#!/bin/bash

# Place script in SD card in Rootfs and Run it with parameter
# Example sudo ./rename_rpi.sh 8
# This would give to RPI new name sim7600prg8

if [ "$#" -eq 0 ]
then
  echo "ERROR: RPI num argument not passed"
  exit 1
fi

NAME="sim7600prg${1}"

echo "New RPI Name: ${NAME}"

cd etc
sudo echo "${NAME}" > hostname

sudo sed -i '$ d' hosts

sudo echo "127.0.0.1  ${NAME}" >> hosts


if rm ../../bootfs/firstrun.sh 2> /dev/null; 
then
  echo "Startup File Deleted"
else 
  echo "Startup File Already Deleted"
fi

