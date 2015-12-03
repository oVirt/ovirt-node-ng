# Installation

To install the Node squashfs image you need a kickstart file which points

## Overview

**FIXME**

- Anaconda for installation
- Important to use Thin LVM


## Anaconda

Anaconda is the installer of Fedora, CentOS, and RHEL.
As stated above, anaconda can use the liveimg as an installation source. And
thin provisioned LVM Logical Volumes can be used as an installation
destination.

Anaconda does not need any modifications to provide the required functional of
this design. All other functionality of anaconda works without limitations.

## Anaconda Boot Options

**FIXME**
Like in "Build Process", important to create a kickstart which points
to the liveimg. Anaconda then needs to use that kickstart

# PXE Installation

**FIXME**

- livecd-iso-to-pxeboot
- Use correct anaconda boot options

# USB Media creation and installation

**FIXME**

1. Fetch a CentOS 7 installation ISO
2. Create a kickstart file using: `echo "liveimg --url=file://ovirt-node-appliance.squashfs.img" > liveimg-install.ks`
3. Run `livecd-iso-to-disk --ks liveimg-install.ks $CENTOS_ISO $DISK`
4. Mount the created disk, and copy the squashfs image to the same directory as the `liveimg-install.ks` file.

