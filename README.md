# Repoman

#### Hey man, let's go hangout and do crimes. Yeah, let's go get software and not pay!
##### https://youtu.be/9bTp6n2qJdI

Repoman is a software sources manager for Debian-based linux distributions. It
allows you to configure system repository information and other system settings,
as well as add, remove, and modify third-party repositories on the system.

Repoman is based on [PPAExtender](https://github.com/mirkobrombin/PPAExtender)

## Requirements
- python3
- libgtk-3-dev
- software-properties-common

## Installation
**Be careful**, modifying PPAs can damage your system.

### From precompiled packages
Repoman can be installed by using the standard package manager:
```
sudo apt update
sudo apt install repoman
```
Additionally, you can use **git**:

```bash
git clone https://github.com/pop-os/repoman.git
cd repoman
sudo python3 setup.py install
```

## Thanks
Very special thanks to [mirkobrombin](https://github.com/mirkobrombin) and
[PPAExtender](https://github.com/mirkobrombin/PPAExtender).
