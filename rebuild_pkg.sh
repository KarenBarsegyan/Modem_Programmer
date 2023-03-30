pyinstaller --onefile -w ModemProgrammer.py
cp dist/ModemProgrammer modem-programmer_pkg/usr/bin/ModemProgrammer 
# dpkg --build modem-programmer_pkg