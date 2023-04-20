# Modem Programmer

SIM7600 programmer for using in Raspberry Pi. This script must be run at any RPI connected to [ScadaToRpiGateway](https://www.google.com) machine. Each RPI in local network must have uniq hostname. This gives an opportunity for ScadaToRpiGateway to communicate with each RPI independently. So, you can start flashing any of SIM76 modems in any time you want.

Next you will see 3 sections:
1. How to set up sim7600 programmer from apt repository (`For users`) <br> 
   You have to do this steps if you want to set up new rpi for flashing modems only 

2. How to set up sim7600 programmer from source (`For developers`) <br>
   You have to do this steps if you want to change sim7600prg source code, test it and make new .deb pkg for all other RPIs 

3. How to make everything from scratch (`For developers`) <br>
   You have to do this steps to understand all design decisions 


# 1) How to set up **sim7600prg** from apt repository?

### Put rpi SD card in uour PC and do next steps:

1. Download latest *sim7600prg* image from [GoogleDrive](https://drive.google.com/drive/folders/1XxYWKCPlGxHbmXVTWYsh-Mkh5s9HJqEX?usp=sharing) and unzip it.

2. Install [RPI Imager](https://www.raspberrypi.com/software/). From linux just run this command:
    
    ``` bash
    sudo apt install rpi-imager
    ```

3. Launch *RPI Imager*, choose recently downloaded sim7600prg.img and SD card. You don't have to manage additional settings (in lover right corner) because it will be replaced with sim7600prg.img settings.

4. Eject SD card and insert it back!!! Sometimes RPI Imager blocks SD card after installing, so you have to reboot it

5. After the end of the process go to sd Rootfs and run rename_rpi.bash with rpi num as argument:
    
    ``` bash
    cd /media/USERNAME/rootfs  
    sudo ./rename_rpi.bash RPI_NUM
    ```

6. Put SD in RPI and start it!


# 2) How to set up **sim7600prg** from source?
    
## First of all do "1) How to set up **sim7600prg** from apt repository?". After that do next:
1. Take off auto startup. Go to rc.local and comment string before "exit 0":
    
    ``` bash    
    sudo nano /etc/rc.local
    ```

2. Install all dependencies:
    
    ``` bash    
    sudo apt update && sudo apt upgrade
    sudo apt install -y pip adb fastboot git
    pip install pyyaml pyserial asyncio websockets
    ```

3. Download Repository
    
    ``` bash
    git clone https://github.com/KarenBarsegyan/Modem_Programmer.git
    ```

4. Now you can run sript from source:

    ``` bash
    cd Modem_Programmer
    python3 StartFlasher.py
    ```

5. Also you can make new .deb package by opening *rebuild_pkg.sh", changing VERSION and RELEASE_NUMBER and running

    ``` bash
    ./rebuild_pkg.sh
    ```

6. Now you can copy sim7600prg_***.deb in apt repository and all other RPI will download and install this version after repower

# 3) How to make everything from scratch?

### Take SD card and install on it any Rasbian you want. Next do this steps:

1. While SD is in your PC open SD bootfs and create ssh file to take on ssh on first RPI start:

    ``` bash
    cd /media/USERNAME/bootfs
    touch ssh  
    ```

2. Place SD in RPI, start it and connect via ssh

3. Install all dependencies:
    
    ``` bash    
    sudo apt update && sudo apt upgrade
    sudo apt install -y pip adb fastboot git
    pip install pyyaml pyserial asyncio websockets
    ```

4. Download Repository
    
    ``` bash
    git clone https://github.com/KarenBarsegyan/Modem_Programmer.git
    ```

5. Add system rights to work with adb device (USB). Open(create) file:
    
    ``` bash
    sudo nano /etc/udev/rules.d/51-android.rules
    ```

6. Add 2 lines and save file:

    ``` bash
    SUBSYSTEM=="usb", ATTR{idVendor}=="1e0e", ATTR{idProduct}=="9001", MODE="0666", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", ATTR{idProduct}=="d00d", MODE="0666", GROUP="plugdev"
    ```

7. ADDITIONAL. If you don't have apt repository server right now, you have to download Sim7600 System files manually. Open terminal in your PC (not on RPI) and copy FlashData from PC to RPI filesystem. If you have apt repo in local network, just go to the `next point`
    
    ``` bash
    scp -r path/to/FlashData/Folder pi@RPI_NAME:/path/to/cloned/repository
    ```

8. If you have apt repo, you have to add its IP to apt search files. But apt repo also has a public key which you need to download. Don't forget to `change` APT_SERVER_IP. In the end just install sim7600prg:
    ``` bash
    cd
    mkdir startup
    cd startup 

    curl http://APT_SERVER_IP/apt-repo/keys/pgp-key.public > pgp-key.public

    echo "deb [arch=all signed-by=/home/pi/startup/pgp-key.public] http://APT_SERVER_IP/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/sim7600prg.list
    ```
    ``` bash
    sudo apt update
    sudo apt install sim7600prg
    ```

9. Setup startup by copying files from folder *startup_files* of this repository to any folder you want (for example *home/pi/startup*)

10. Open rc.local file and add startup script run command before exit 0:
    ``` bash
    sudo nano /etc/rc.local
    ```
    ``` bash
    <!-- Command to write into rc.local -->
    sudo bash -c 'bash /home/pi/startup/startup.sh  > /home/pi/startup/startup.log 2>&1' &
    ```

11. Now you can start script from source and from apt repo with auto update