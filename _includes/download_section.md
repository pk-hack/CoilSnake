<span class="topright">Latest Version: {{site.latest_version}}</span>

## Download 

On Windows, just [download the .exe]({{site.windows_download_url}}). Linux users may install from source:

    $ sudo apt-get install python3-pip python3-dev g++ libyaml-dev \
                           python3-tk python3-pil.imagetk \
                           libjpeg-dev zlib1g-dev tk8.6-dev tcl8.6-dev
    $ git clone https://github.com/mrtenda/CoilSnake.git
    $ cd CoilSnake
    $ make
    $ sudo make install
    $ coilsnake
