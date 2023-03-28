# What to do with clear Rasbian to start Modem Flasher?

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

---------------------------------------------------------- 

### Connect to RPI via ssh and do next steps:

1. Install all dependencies:

    ``` bash    
    sudo apt update && sudo apt upgrade
    sudo apt install pip adb fastboot git
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
