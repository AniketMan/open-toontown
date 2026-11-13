#!/bin/sh
cd ..

export LOGIN_TOKEN=dev

"${PYTHON:-python3.9}" -m toontown.launcher.QuickStartLauncher
