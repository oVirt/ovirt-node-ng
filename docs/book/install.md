# Installation

To install the Node squashfs image you need a kickstart file.

## Overview

`Anaconda` is the installation program used by Fedora, Red Hat Enterprise Linux,
CentOS and some other distributions. It allows the user to install the operating
system software on the target computer. Additionally, it can also upgrade existing
installations of earlier versions of the same distribution.

### Highlight features that ovirt-node-appliace take advance of Anaconda:

* Automatically create partitions

* `LVM Thin Provisioning` support helps users to make snapshot and
rollbacks in the system.

* Install disk image instead of packages.

Anaconda does not need any modifications to provide the required functional of
this design. All other functionality of Anaconda works without limitations.

## Anaconda Kickstart

The Anaconda kickstart is an automated installation method to install operating system.

System administrator and/or developers can create a single file (.ks) containing the answers
to all the questions that would normally be asked during a typical installation.

The minimal requirement kickstart options are `liveimg` and the correct partitioning.
Anaconda then will use that kickstart to proceed with the installation.

In the `liveimg` option it can be the `squashfs.img` from a Live iso,
or any filesystem mountable by the install media (eg. ext4).

**NOTE**: Using only minimal kickstart requirement options (`liveimg` and partitioning)
will trigger the manual installation. For more detailed information about kickstart
options or automatic installations, please see official kickstart documentation.

## Anaconda Boot Options

To start a Kickstart installation, a special boot option `inst.ks=` must be specified
when booting the system.

# Example: Manual installation of Node from a webserver

## Install httpd

`httpd` must be installed on a separate host

    $ sudo yum -y install httpd
    $ sudo systemctl start httpd
    $ sudo systemctl enable httpd

## Publish the `squashfs` image

Build locally the ovirt-node-ng squashfs image or download
the last successfully image from ovirt jekins job and make it available
in the httpd server.

    $ cd /var/www/html
    $ wget http://jenkins.ovirt.org/job/ovirt-appliance-node_master_create-squashfs-el7_merged/lastSuccessfulBuild/artifact/exported-artifacts/ovirt-node-ng-image.squashfs.img

## Create the kickstart

Create the minimal-ngn.ks in the httpd public dir

    $ cat minimal-ngn.ks
    # FIXME This should be fixed more elegantly with https://bugzilla.redhat.com/663099#c14
    # At best we could use: autopart --type=thinp
    reqpart --add-boot
    part pv.01 --size=50000 --grow
    volgroup HostVG pv.01
    logvol swap --vgname=HostVG --name=swap --fstype=swap --recommended
    logvol none --vgname=HostVG --name=HostPool --thinpool --size=30000 --grow
    logvol /    --vgname=HostVG --name=root --thin --poolname=HostPool --fsoptions="discard" --size=5000
    logvol /var --vgname=HostVG --name=var --thin --poolname=HostPool --fsoptions="discard" --size=15000
    
    liveimg --url=http://server/ovirt-node-ng-image.squashfs.img

## Start the installation

At this stage, you should be able to proceed with the manual installation adding
into the boot kargs the kickstart flag inst.ks=http://server/minimal-ngn.ks

# PXE Installation

**FIXME**

- livecd-iso-to-pxeboot
- Use correct anaconda boot options

# USB Media creation and installation

**FIXME**

1. Fetch a CentOS 7 installation ISO
2. Create a kickstart file using: `echo "liveimg --url=file://ovirt-node-ng-image.squashfs.img" > liveimg-install.ks`
3. Run `livecd-iso-to-disk --ks liveimg-install.ks $CENTOS_ISO $DISK`
4. Mount the created disk, and copy the squashfs image to the same directory as the `liveimg-install.ks` file.

# Additional reference

Kickstart Documentation
https://github.com/rhinstaller/pykickstart/blob/master/docs/kickstart-docs.rst
