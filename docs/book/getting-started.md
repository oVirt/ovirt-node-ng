# Getting started

The following steps will tell you how to build and install the Node image into
a VM for testing.

## Prerequisities

Node is mainly developed on rpm based distributions like Fedora and CentOS 7.
The main requirements are

- git
- qemu
- libguestfs
- python


## Bootstrap

The starting point is the `ovirt-node-appliance` which is currently living in
the `ovirt-appliance` repository:

    git clone git://gerrit.ovirt.org/ovirt-appliance.git
    git submodule update --init --recursive

    cd node-appliance


## Building the image

To build the `ovirt-node-appliance.squashfs.img` image from the
`ovirt-node-appliance.ks` you now just need to run the following command and
be patient:

    # To build the squashfs image (liveimg):
    make image-build

**NOTE:** This will download a lot of packages from the internet

The now available squashfs image can not directly be booted.
It can only be fed to dracut for booting, or to anaconda for installation.


## Installing and booting the image

To be able to boot the squashfs, you first need to install it.
This can be done by running:

    make image-install

This will install the previously generated squashfs image to the
`ovirt-node-appliance-auto-install.qocw2` disk image.
The auto-installation ensures that LVM Thin is used, otherwise the upgrade and
rollbacks would not work.

This disk image can be booted in KVM and used for debugging and testing.

**NOTE:** A root password can be set in the
`ovirt-node-appliance-auto-install.ks.in` kickstart _before_ the install.


## Making Changes

The appliance image itself is defined by the `ovirt-node-appliance.ks` file.
Any change to that file will lead to a change in the appliance.

Note that some changes (i.e. root password) might be overriden or deactivated
at installation time by directives in the
`ovirt-node-appliance-auto-installation.ks`.

Once you did a change you can commit the change and post it to
[oVirt Gerrit](http://gerrit.ovirt.org) for review.
