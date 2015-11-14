exec { "apt-get update":
  path => "/usr/bin",
}

$dependencyPackages = ["make", "git", "python-pip", "vim", "python-dev", "libyaml-dev", "python-tk", "g++", "libboost-filesystem-dev", "libboost-python-dev", "libjpeg-dev", "zlib1g-dev", "tk8.5-dev", "tcl8.5-dev"]

package { $dependencyPackages:
  ensure => present,
  provider => apt,
  require => Exec["apt-get update"],
}
