# Modem Programmer

SIM7600 programmer for using in Raspberry Pi. This script must be run at any RPI connected to [ScadaToRpiGateway](https://www.google.com) machine. Each RPI in local network must have uniq static IP. This gives an opportunity for ScadaToRpiGateway to communicate with each RPI independently. So, you can start flashing of SIM76 from any RPI in any time you want.

Next you will see 3 sections:
1. Setup Rasbian
2. How to start ModemProgrammer from apt repository (`For users`)
3. How to start ModemProgrammer from source (`For developers`)

**You have to do section 1 and one of sections 2 or 3.** Choose **Section 2** if you want to start new RPI or **Section 3** if you want to edit ModemProgrammer code

# 1) What to do with clear Rasbian?

### Put sd into PC and do next steps:

1. Take on SSH by adding empty file named 'ssh' to boot

    ``` bash
    cd /media/sd/boot
    touch ssh
    ```

2. Navigate to the SD card’s rootfs directory and edit /etc/dhcpcd.conf

    ``` bash
    cd /media/sd/rootfs/etc
    nano dhcpcd.conf
    ```
3. Add static IP settings in the end of file. N depends on current RPI number. Use numbers from 2 to 254
    
    ``` bash
    interface eth0
    static ip_address=192.168.4.2/24
    static routers=192.168.4.1
    static domain_name_servers=192.168.4.1
    ```

4. Put SD into RPI, take power ON and plug ethernet

# 2) What to do to start Modem Flasher **From APT Repository** and make it run in startup?

### Connect to RPI via ssh and do next steps:

1. Install all dependencies:
   
    ``` bash    
    sudo apt update && sudo apt upgrade
    sudo apt install -y adb fastboot
    ```

2. Let APT know ModemProgrammer repository adress. For this make new file in apt source folder with next command:
   
    ``` bash
    sudo echo "deb [arch=all] http://192.168.4.1:8000/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/ModemProgrammer.list
    ```

3. Install ModemProgrammer:
    
    ``` bash
    sudo apt-get update --allow-insecure-repositories
    sudo apt-get install modemprogrammer
    ```

4. Create startup file for auto update and start ModemProgrammer pkg
    
    ``` bash
    mkdir ~/StartupProgrammer
    echo "sudo apt-get update --allow-insecure-repositories
    sudo apt-get upgrade modemprogrammer
    ModemProgrammer
    " > ~/StartupProgrammer/startup.sh && chmod +x ~/StartupProgrammer/startup.sh
    ```

5. Include startup.sh in startup list with *cron*. Run this command:

    ``` bash
    crontab -e
    ```

    Add this string to the end of file and exit with saving:

    ``` bash
    @reboot sudo sh ~/StartupProgrammer/startup.sh
    ``` 

6. Now you can restart yor Pi!

# 3) What to do to start Modem Flasher **From Source**?

### Connect to RPI via ssh and do next steps:

1. Install all dependencies:
    
    ``` bash    
    sudo apt update && sudo apt upgrade
    sudo apt install -y pip adb fastboot git
    pip install pyyaml pyserial asyncio websockets
    ```

2. Download Repository
    
    ``` bash
    git clone https://github.com/KarenBarsegyan/Modem_Programmer.git
    ```

3. Open terminal in your PC (not on RPI) and copy FlashData from PC to RPI filesystem (**N** depends on current RPI static IP)
    
    ``` bash
    scp -r path/to/FlashData/Folder pi@192.168.4.N:/path/to/cloned/repository
    ```

4. Go back to RPI terminal. Add system rights to work with adb device (USB). Firstly, open(create) file:
    
    ``` bash
    sudo nano /etc/udev/rules.d/51-android.rules
    ```

5. Add 2 lines and save file:

    ``` bash
    SUBSYSTEM=="usb", ATTR{idVendor}=="1e0e", ATTR{idProduct}=="9001", MODE="0666", GROUP="plugdev"
    SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", ATTR{idProduct}=="d00d", MODE="0666", GROUP="plugdev"
    ```

4. Modify *configuration.yaml* file in repository folder to set your work settings
