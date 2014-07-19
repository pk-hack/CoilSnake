<span class="topright">Latest Version: {{site.latest_version}}</span>

## Download 

On Windows, just [download the .exe]({{site.windows_download_url}}). Linux users may install from source:

    $ sudo apt-get install python-pip python-dev libyaml-dev python-tk \
                           g++ libboost-filesystem-dev libboost-python-dev \
                           libjpeg-dev zlib1g-dev tk8.5-dev tcl8.5-dev
    $ git clone https://github.com/kiij/CoilSnake.git
    $ cd CoilSnake
    $ make
    $ sudo make install
    $ coilsnake
