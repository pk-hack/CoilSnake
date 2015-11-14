# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.define "ubuntu" do |ubuntu|
    ubuntu.vm.box = "precise32"

    ubuntu.vm.provision :puppet

    ubuntu.vm.provision :puppet do |puppet|
      puppet.manifest_file  = "default.pp"
    end
  end

  config.vm.define "windows" do |windows|
    box_name = "win7-ie11"
    box_repo = "http://aka.ms"

    windows.vm.box = "modern.ie/" + box_name
    windows.vm.box_url = box_repo + "/vagrant-" + box_name
    windows.vm.boot_timeout = 500

    windows.vm.network "forwarded_port", guest: 3389, host: 3389, id: "rdp", auto_correct: true

    # winrm config, uses modern.ie default user/password. If other credentials are used must be changed here
    windows.vm.communicator = "winrm"
    windows.winrm.username = "IEUser"
    windows.winrm.password = "Passw0rd!"

    windows.vm.provider "virtualbox" do |vb|
      vb.gui = true
      vb.customize ["modifyvm", :id, "--memory", "1024"]
      vb.customize ["modifyvm", :id, "--vram", "128"]
      vb.customize ["modifyvm", :id,  "--cpus", "2"]
      vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize ["guestproperty", "set", :id, "/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold", 10000]
    end
  end
end
