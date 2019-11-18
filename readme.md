# DjHome
Smart home application that takes into consideration Jewish holidays.

## Overview
* Configure via /admin
* Use the OurHome mobile app
* Install PhigetServer per demand

## Deployment
Note: Instructions are specifically detailed for Raspberry Pi Raspbian.

### Update OS
    sudo raspi-config --> Set timezone
    sudo apt-get update && sudo apt-get upgrade -y

### Python 3.6
Make sure you have Python 3.6 installed.\
If not, install from [here](https://gist.github.com/dschep/24aa61672a2092246eaca2824400d37f)

* Packages that can be removed after Python 3.6 installation:
    ```
    sudo apt-get --purge remove -y bzip2-doc fontconfig-config fonts-dejavu-core libbz2-dev:armhf libdb5.3-dev libdrm-amdgpu1:armhf libdrm-freedreno1:armhf libdrm-nouveau2:armhf libdrm-radeon1:armhf
    sudo apt-get --purge remove -y libexpat1-dev:armhf libfontconfig1:armhf libfontconfig1-dev:armhf libfontenc1:armhf libgdbm-dev:armhf libgl1-mesa-dri:armhf libgl1-mesa-glx:armhf libglapi-mesa:armhf 
    sudo apt-get --purge remove -y libice-dev:armhf libice6:armhf libllvm3.9:armhf liblzma-dev:armhf libncurses5-dev:armhf libncursesw5-dev:armhf libpthread-stubs0-dev:armhf libreadline-dev:armhf 
    sudo apt-get --purge remove -y libsensors4:armhf libsm-dev:armhf libsm6:armhf libsqlite3-dev:armhf libtcl8.6:armhf libtinfo-dev:armhf libtk8.6:armhf libtxc-dxtn-s2tc:armhf
    sudo apt-get --purge remove -y libutempter0:armhf libx11-dev:armhf libx11-doc libx11-xcb1:armhf libxau-dev:armhf libxaw7:armhf libxcb-dri2-0:armhf libxcb-dri3-0:armhf libxcb-glx0:armhf libxcb-present0:armhf
    sudo apt-get --purge remove -y libxcb-shape0:armhf libxcb-sync1:armhf libxcb1-dev:armhf libxcomposite1:armhf libxdamage1:armhf libxdmcp-dev:armhf libxext-dev:armhf libxfixes3:armhf libxft-dev libxft2:armhf
    sudo apt-get --purge remove -y libxi6:armhf libxinerama1:armhf libxmu6:armhf libxpm4:armhf libxrandr2:armhf libxrender-dev:armhf libxrender1:armhf libxshmfence1:armhf libxss-dev:armhf libxss1:armhf 
    sudo apt-get --purge remove -y libxt-dev:armhf libxt6:armhf libxtst6:armhf libxv1:armhf libxxf86dga1:armhf libxxf86vm1:armhf tcl tcl-dev:armhf tcl8.6 tcl8.6-dev:armhf tk tk-dev:armhf tk8.6 tk8.6-dev:armhf 
    sudo apt-get --purge remove -y x11-common x11-utils x11proto-core-dev x11proto-input-dev x11proto-kb-dev x11proto-render-dev x11proto-scrnsaver-dev x11proto-xext-dev xbitmaps xorg-sgml-doctools xterm xtrans-dev
    sudo apt-get autoremove
    sudo apt-get clean
    ```

### Django project
1. Download source files to ```/home/pi/djhome```

1. Create the log directory:
    ```
    mkdir log
    chmod g+w log
    chmod g+s log
    ```

### Packages
    sudo apt-get install python3-dev python3-venv python3-pip -y
    sudo apt-get install build-essential -y               #for twisted, used by django channels
    sudo apt-get install redis-server -y                  #for django channels and rq
    sudo apt-get install libffi-dev -y                    #for twisted tls
    
    #You will want to activate your virtual-environment at this point
    pip install -r requirements.txt
    #Note: Needed by Twisted ssl: sudo apt-get install -y libssl-dev
    pip install -U Twisted[tls,http2]
   
    python manage.py collectstatic

### Service and Process Manager
(do not run in a virtual-env)

    sudo -H pip3 install circus chaussette
    
    sudo ln -s /home/pi/djhome/djhome/scripts/djhome.service /etc/systemd/system/djhome.service
    sudo systemctl enable djhome.service
    echo 'Environment="DJANGO_DEBUG=false"' > tmp
    sudo env SYSTEMD_EDITOR="cp tmp" systemctl edit djhome.service
    rm tmp
    sudo systemctl enable djhome.service
    sudo service djhome start

    #test:  sudo /usr/local/bin/circusd /home/pi/djhome/circus.ini
    #logs: journalctl -u djhome -f


## License
Licensed under the AGPL-3.0 License - see [LICENSE](LICENSE) for details
