# DjHome
Smart home application that takes into consideration Jewish holidays.

## Overview
* Configure via /admin
* Use the OurHome mobile app
* Install PhigetServer per demand

## Deployment
Instructions are specifically detailed for Raspberry Pi Raspbian.
### Prerequisites
    sudo raspi-config --> Set timezone
    sudo apt-get update && sudo apt-get upgrade -y
    sudo apt-get install python3-dev python3-venv python3-pip -y
    sudo apt-get install build-essential -y               #for twisted, used by django channels
    #sudo apt-get install rabbitmq-server -y              #for celery. consider using redis (needed for channels) un/pw: test/test  http://10.100.101.21:15672
    sudo apt-get install redis-server -y
    sudo apt-get install libffi-dev -y                    #for twisted tls
    pip install -r requirements.txt
    pip install -U Twisted[tls,http2]


1. Create the log directory:
    ```
    mkdir log
    chmod g+w log
    chmod g+s log
    ```
1. Service and Process Manager\
(do not run in a virtual-env)
    ```
    sudo -H pip3.6 install circus
    sudo -H pip3.6 install chaussette
    sudo ln -s /home/pi/djhome/djhome/scripts/djhome.service /etc/systemd/system/djhome.service
    sudo systemctl edit djhome.service
        update: Environment="DJANGO_DEBUG=false"

    sudo systemctl enable djhome.service

    test:  sudo /usr/local/bin/circusd /home/pi/djhome/circus.ini
    logs: journalctl -u djhome -f
    ```

1. Django
    ````
    python manage.py collectstatic
    ````

## License
Licensed under the AGPL-3.0 License - see [LICENSE](LICENSE) for details
