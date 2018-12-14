#!/bin/bash

test -f LinkBox-macintosh-64bit.dmg && rm LinkBox-macintosh-64bit.dmg

create-dmg \
--volname "LinkBox Installer" \
--volicon "icon.icns" \
--background "static/design/mac_installer_background.png" \
--window-pos 200 120 \
--window-size 640 480 \
--icon-size 64 \
--icon "LinkBox.app" 190 340 \
--hide-extension "LinkBox.app" \
--app-drop-link 450 340 \
"LinkBox-macintosh-64bit.dmg" \
"LinkBox/"

