exec { "apt-update":
  command => "/usr/bin/apt-get update"
}

# Ensure apt-get update has been run before installing any packages
Exec["apt-update"] -> Package <| |>

$dependencyPackages = ["make", "git", "python3-pip", "vim", "python3-dev", "libyaml-dev", "python3-tk", "g++", "libjpeg-dev", "zlib1g-dev", "tk8.6-dev", "tcl8.6-dev"]

package { $dependencyPackages:
  ensure => present,
  provider => apt
}
