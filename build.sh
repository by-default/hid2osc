#!/usr/bin/env bash

mkdir -p build/usr/bin
mkdir -p build/etc/hid2osc
mkdir -p build/etc/systemd/system
cp hid2osc.py build/usr/bin/hid2osc
cp config.yaml.example build/etc/hid2osc
cp hid2osc.service build/etc/systemd/system
chmod +x build/usr/bin/hid2osc
