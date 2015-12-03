# Build process

In the [getting started section](getting-started.md) it was shown that the
following command will perform the image build:

    make image-build

In this section we will review this build process in-depth.

## Overview

From a high level view the build process is simple: A kickstart is passed
to `livemedia-creator` which is in turn building the appliance image.

![](imgs/build-flow.dot.png)

Let's start with the specifics about the kickstart file.


## Kickstart
The _kickstart_ file defines what packages go into the appliance image. In
addition a few additional configurations can be performed as part of the
installation.

A kickstart file is used, because anaconda is used for installation. And
kickstarts are files which control unattended installations.

See the [official kickstart documentation](https://github.com/rhinstaller/pykickstart/blob/master/docs/kickstart-docs.rst)
for more informations.

The specific kickstart which defines the oVirt Node appliance is defined in the
`node-appliance/ovirt-node-appliance.ks` file, which hosted in the
`ovirt-appliance` repository.
See the [getting started section](getting-started.md) for how to clone that
repository.

### Unattended installation
The first important note about the Node kickstart is, that it needs to contain
enough informations to perform an [unattended installation](https://github.com/rhinstaller/pykickstart/blob/master/docs/kickstart-docs.rst#creating-the-kickstart-file).

There are "enough informations" if the kickstart provides answers to all
required spokes.

### Security
To have a decent level of security, the image comes with:

+ SELinux in permissive mode (during development)
+ A locked _root_ account
+ A locked _node_ account, which should get unlocked during installation

The following directives are used to achieve this:

    selinux --permissive
    rootpw --lock
    user --name=node --lock

### Filesystem
It is important that the kickstart will only create a disk with a single
partition, because this single partition will get extracted and be wrapped
into the squashfs.

Another important point is to choose a filesystem which supports _discard_ or
_trim_. This feature enables alter - after deployment - an efficient use of
the available space, and is a curcial point in the upgrade and rollback
implementation. See the [upgrade section](upgrade.md) for more details on
the storage requirements.

The following directives are used to ensure that only a single ext4 partition
with _discard_ support is used:

    clearpart --all --initlabel
    part / --size=3072 --fstype=ext4 --fsoptions=discard

### Packages
The `%packages` section defines what packages get installed inside the
appliance image.
The main goal should be to keep this list small.

If you see yourself adding packages to this kickstart section, then you should
ask yourself, why this package you are adding, isn't a dependency of an already
included package.

Let's take a look at the important packages:
    
    %packages
    # config generic == not-hostonly, this is needed
    # to support make a generic image (do not keep lvm informations in the image)
    dracut-config-generic
    
    # EFI support
    grub2-efi
    shim
    efibootmgr

    lvm2
    imgbased
    %end

The packages are used to achieve the following:

+ Add EFI support
+ Add generic initramfs support
+ Add lvm2 and imgbased support

On normal installs of Fedora or CentOS these packages don't need to be added
explicitly, because anaconda will install them autoamitcally if they are
needed.
`lvm2` will be installed if LVM is used for storage, `grub2-efi` will be
installed if the OS is installed on EFI hardware, etc.

We need to install these packages explicitly, because it is expected that the
applianc eimage contains everything that is needed for every use-case.

**FIXME** The package requirements should go to some package dependencies,
i.e. `ovirt-release-node-host`, see [this bug](https://bugzilla.redhat.com/show_bug.cgi?id=1285024).

### `%post` scriptlets for additional software

You might have noticed that i.e. `vdsm` is missing in the package list above.

`vdsm` can not be installed directly, because it needs the ovirt`-release`
package to be installed, to get access to the necessary repositories.

That is why `vdsm` is getting installed in a `%post` scriptlet.

## Installation

Now that the kickstart is ready, it is passed to anaconda inside the VM to
install the required packages onto disk.

Let's see how this step looks in-depth.

## Anaconda arguments

The key is to get anaconda to do an unattended install based on the kickstart.
To achieve this you need to pass the following arguments to anaconda:

    inst.cmdline inst.ks=<url-to-ks> inst.stage2=live:CDLABEL=CentOS\x207\x20x86_64

This assumes that a CentOS 7 installation ISO is attached to the VM.

See the [anaconda boot options documentation](https://github.com/rhinstaller/anaconda/blob/master/docs/boot-options.rst)
for the details of those arguments.


Before we continue: Both of the methods described below are using the same
basic mechanism to perform the installation.
They only differ in additional logic around pre- and post-processing of the
kickstart and the final image.

## Current build process: `image-tools`

The `image-tools` script collection is mimicing the behavior of
`livemedia-creator`, the main difference is that `image-tools` are using
qemu directly, to be able to use this scripts in Jenkins.

To get started, you can clone the `image-tools`

    git clone https://github.com/fabiand/image-tools

The main build logic is in the `anaconda_install` script.
This script will then perform the installation as described previously.

**FIXME** this tool should be obsoleted by koji and livemdia-creator


### Image Format: Liveimg

Node is installed (and updated) using a single operating system image.
Contrary to many other distributions packages are not used to install the operating system. Packages are primarily used to [build the image](build.md), and eventually to [customize the image](impl.md).

The liveimg image format is a Fedora- and CentOS-ish format used to deliver LiveCDs.
A liveimg is a file-system image wrapped into a squashfs image.
The reasoning behind this matroska mechanism is that the file-system image can be mounted easily, and the squashfs image - as it can compress - is helping to reduce the size of the image.
Because it has been around for a long time, this format has mature support in dracut and anaconda.
This effectively enables two use-cases with one image:

* anaconda can use this image as a source instead of individual rpms
* dracut can boot into a liveimg


## Deliveryformat

The appliance image is delivered in the squashfs liveimg format.

This format is understood by anaconda (for installation) and dracut (for state- and diskless boots).

The format is described in `man dracut.cmdline`:

    The filesystem structure is expected to be:

       squashfs.img          |  Squashfs downloaded via network
          !(mount)
          /LiveOS
              |- ext3fs.img  |  Filesystem image to mount read-only
                   !(mount)
                   /bin      |  Live filesystem
                   /boot     |
                   /dev      |
                   ...       |

> Note: the `ext3fs.img` is a file-system image, not a disk image.

The `ext3fs.img` can be created using a range of tools, the primary one being `livemedia-creator` (part of `lorax`).

[Eventually](https://bugzilla.redhat.com/show_bug.cgi?id=1282496) `livemedia-creator` will be capable of creating squashfs images directly.
