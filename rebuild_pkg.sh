#!/bin/sh

VERSION=0.0.1
RELEASE_NUMBER=1

echo "Build pkg with version ${VERSION}"

rm *.deb
rm -r sim7600prg*

mkdir -p "sim7600prg_${VERSION}-${RELEASE_NUMBER}_all/usr/bin/"
mkdir -p "sim7600prg_${VERSION}-${RELEASE_NUMBER}_all/DEBIAN"

echo "Package: sim7600prg
Version: ${VERSION}
Maintainer: karen.barsegyan-2001@bk.ru
Depends: libc6
Architecture: all
Description: SIM7600 Flasher" \
> "sim7600prg_${VERSION}-${RELEASE_NUMBER}_all/DEBIAN/control"

pyinstaller --onefile -w StartFlasher.py
cp "dist/StartFlasher" "sim7600prg_${VERSION}-${RELEASE_NUMBER}_all/usr/bin/sim7600prg"
dpkg --build "sim7600prg_${VERSION}-${RELEASE_NUMBER}_all"