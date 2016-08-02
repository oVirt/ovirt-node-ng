# Getting started

The following steps will tell you how to build the Node image, and install it
into a virtual machine for testing.

## Prerequisities

Node is mainly developed on RPM-based distributions like Fedora and CentOS 7.
The main requirements are:

-   git
-   qemu
-   python
-   python-requests
-   python-pep8
-   pyflakes
-   python-nose
-   python-sh
-   libguestfs
-   libguestfs-tools
-   libvirt-python
-   lorax
-   virt-install

## Bootstrap

The starting point is `ovirt-node-ng` which is currently living in
the `ovirt-node-ng` repository on[oVirt Gerrit](http://gerrit.ovirt.org):

    git clone git://gerrit.ovirt.org/ovirt-node-ng.git
    git submodule update --init --recursive

## Building the image

To build the `ovirt-node-ng-image.squashfs.img` image with the default
configuration from `ovirt-node-ng-image.ks`, you now just need to run the
following command and be patient:

    # To build the squashfs image (liveimg):
    make squashfs

**NOTE:** This will download a lot of packages from the internet

The now available squashfs image can not directly be booted, but it can be
examined with libguestfs or guestfish. For example, to get a list of installed
packages:

    guestfish --ro -a ovirt-node-ng-image.squashfs.img
    run
    mount /dev/sda /
    mount-loop /LiveOS/rootfs.img
    sh "rpm -qa"

For use, it can only be fed to dracut for booting, or to anaconda for
installation.

## Installing and booting the image

In order to boot the squashfs, you first need to install it.
This can be done automatically by running:

    make installed-squashfs

This will install the previously generated squashfs image to a file named
`installed-ovirt-node-ng-squashfs.raw`, as a usable disk image.

The auto-installation ensures that LVM thin pools are used, otherwise the
upgrade and rollbacks would not work. oVirt Node relies on thin pools and
volumes in order to install updates side-by-side.

This disk image can be booted in KVM, and can be used for debugging and testing.

**NOTE:** A root password can be set in the
`ci-image-install.ks` kickstart _before_ the install.

You can also generate an installable ISO with `make offline-installation-iso`

## Making Changes

The appliance image itself is defined by the `ovirt-node-ng-image.ks`
file. Any change to that file will lead to a change in the generated squashfs.

Note that some changes (i.e. root password) might be overriden or deactivated
at installation time by directives in the `ci-image-install.ks`, which is used
to generate the disk image.

If you made a change you would like to contribute, you can commit it and post
it to [oVirt Gerrit](http://gerrit.ovirt.org) for review. Instructions for
[working with oVirt Gerrit](
  http://www.ovirt.org/develop/dev-process/working-with-gerrit/)
are available if you have not contributed before.
