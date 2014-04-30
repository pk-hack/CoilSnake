<span class="topright">Latest Version: {{site.latest_version}}</span>

## Download 

On Windows, just [run the installer]({{site.windows_download_url}}). On Linux, download and install from source:

    $ sudo apt-get install python-pip python-dev libyaml-dev python-tk \
                           g++ libboost-filesystem-dev
    $ git clone https://github.com/kiij/CoilSnake.git
    $ cd CoilSnake
    $ make
    $ sudo make install
    $ coilsnake
