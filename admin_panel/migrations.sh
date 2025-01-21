#!/usr/bin/env bash

python3 /opt/app/manage.py migrate movies --fake 2>/dev/null
python3 /opt/app/manage.py createsuperuser --no-input 2>/dev/null
exit 0