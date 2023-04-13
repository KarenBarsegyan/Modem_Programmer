# Modem Programmer

SIM7600 programmer for using in Raspberry Pi. This script must be run at any RPI connected to [ScadaToRpiGateway](https://www.google.com) machine. Each RPI in local network must have uniq static IP. This gives an opportunity for ScadaToRpiGateway to communicate with each RPI independently. So, you can start flashing of SIM76 from any RPI in any time you want.

Next you will see 23 sections:
1. How to set up sim7600 programmer from apt repository (`For users`) <br> 
   You have to do this steps if you want to set up new rpi for flashing modems only 

2. How to set up sim7600 programmer from source (`For developers`) <br>
   You have to do this steps if you want to change sim7600prg source code, test it and make new .deb pkg for all other RPIs 

3. How to make everything from scratch (`For developers`) <br>
   You have to do this steps to understand all design decisions 


# 1) How to set up **sim7600prg** from apt repository?

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

# 2) How to set up **sim7600prg** from source?
    
1. dssd

    ``` bash
    sudo bash -c 'bash /home/pi/startup/startup.sh  > /home/pi/startup/startup.log 2>&1' &
    ```

# 3) How to make everything from scratch?

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
