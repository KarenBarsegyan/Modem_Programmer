#!/bin/sh

VERSION=0.0.3
RELEASE_NUMBER=1

echo "Build pkg with version ${VERSION}"

rm *.deb
rm -r modem-programmer_*

mkdir -p "modem-programmer_${VERSION}-${RELEASE_NUMBER}_all/usr/bin/"
mkdir -p "modem-programmer_${VERSION}-${RELEASE_NUMBER}_all/DEBIAN"

echo "Package: ModemProgrammer
Version: ${VERSION}
Maintainer: karen.barsegyan-2001@bk.ru
Depends: libc6
Architecture: all
Description: SIM76 Flasher" \
> "modem-programmer_${VERSION}-${RELEASE_NUMBER}_all/DEBIAN/control"

pyinstaller --onefile -w ModemProgrammer.py
cp "dist/ModemProgrammer" "modem-programmer_${VERSION}-${RELEASE_NUMBER}_all/usr/bin/ModemProgrammer"
dpkg --build "modem-programmer_${VERSION}-${RELEASE_NUMBER}_all"