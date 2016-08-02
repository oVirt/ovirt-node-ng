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
addition, a few additional configuration steps can be performed as part of the
installation.

A kickstart file is used because anaconda is used for installation, and
kickstart can be used for deep, repeatable customization with anaconda, or
for simple automated installs.

See the [official kickstart documentation](https://github.com/rhinstaller/pykickstart/blob/master/docs/kickstart-docs.rst)
for more informations.

The specific kickstart which defines the oVirt Node appliance is defined in the
`ovirt-node-ng-image.ks` file, which hosted in the`ovirt-node-ng` repository.
See the [getting started section](getting-started.md) for how to clone that
repository.

### Unattended installation

The first important note about the Node kickstart is that it needs to contain
enough directives to perform an [unattended installation](https://github.com/rhinstaller/pykickstart/blob/master/docs/kickstart-docs.rst#creating-the-kickstart-file).

There are "enough directives" if the kickstart provides answers to all spokes
(anaconda's terminology for a configuration section). You will know whether
there is enough information by watching the installer. If there are spokes
which are not completed, directives which fill those spokes will need to be
added. If the `text` directive is used in the kickstart, spokes which are
complete will helpfully have `[x]` next to them. Those which do not will show
`[ ]`.

### Security

To provide a baseline level of security, the image comes with:

+   SELinux in permissive mode (during development)
+   A locked _root_ account
+   A locked _node_ account, which should get unlocked during installation

The following directives are used to achieve this:

    selinux --permissive
    rootpw --lock
    user --name=node --lock

### Filesystem

It is important to note that the kickstart will only create a disk with a
single partition, because this partition will be extracted and be wrapped
in the squashfs.

Another important point is the choide of a filesystem which supports _discard_
or _trim_. This feature enables alter - after deployment - an efficient use of
the available space, and is a crucial point in the upgrade and rollback
implementation. See the [upgrade section](upgrade.md) for more details on
the storage requirements.

The following directives are used to ensure that only a single ext4 partition
with _discard_ support is used:

    clearpart --all --initlabel
    part / --size=3072 --fstype=ext4 --fsoptions=discard

### Packages

The `%packages` section defines what packages get installed inside the
appliance image.
The primary goal should be to keep this list small.

If you find yourself adding packages to this kickstart section, you should ask
yourself why the package you are adding isn't a already a dependency of an
included package. If it isn't, is it necessary for inclusion? If you believe
that it is, submit a patch which includes it as a dependency of
`ovirt-node-node-host` or some upstream package which is already included.

Let's take a look at the important packages:

    %packages
    @anaconda-tools
    dracut-config-generic
    -dracut-config-rescue
    %end

### Additional software

You may have noticed that this list of packages is far too small to achieve the
functionality offered by oVirt Node.

The explanation is in the %post section:

    # Adding upstream oVirt vdsm
    # 1. Install oVirt release file with repositories
    yum install -y --nogpgcheck http://plain.resources.ovirt.org/pub/ovirt-4.0-pre/rpm/el7/noarch/ovirt-release40-pre.rpm

    # 2. Install oVirt Node release and placeholder
    # (exclude ovirt-node-ng-image-update to prevent the obsoletes logic)
    yum install -y --nogpgcheck \
      --exclude ovirt-node-ng-image-update \
      ovirt-release-host-node \
      ovirt-node-ng-image-update-placeholder

First, we install the ovirt-release RPM, which adds all the repositories needed
to install additional software.

After this, only two packages are installed:

+   `ovirt-node-ng-image-update-placeholder` -- This is present to provide a
target for `yum update`, as it's obsoleted by `ovirt-node-ng-image-update`

+   `ovirt-release-host-node` -- All of the dependencies for oVirt Node are
contained in `ovirt-release-host-node`, including EFI support, `vdsm`, and
the other required tooling to product a functional system.

The packages are used to achieve the following:

+   Add EFI support
+   Add generic initramfs support
+   Add lvm2 and imgbased support

On normal installs of Fedora or CentOS, these packages don't need to be added
explicitly, because anaconda will install them automatically if they are
needed.

`lvm2` will be installed if LVM is used for storage, `grub2-efi` will be
installed if the OS is installed on EFI hardware, etc.

We need to install these packages explicitly, because it is expected that the
appliance image contains everything that is needed for every use-case, and we
want to include support for configurations which differ from the install
environment, which, as noted above, only has one partition, and
livemedia-creator does not install in EFI mode.

## Installation

Now that the kickstart is ready, it is passed to anaconda inside the VM to
install the required packages onto disk.

Let's see how this step looks in-depth.

Before we continue: both of the methods described below are using the same
basic mechanism to perform the installation. They only differ in additional
logic around pre- and post-processing of the kickstart and the final image.

## Current build process: `livemedia-creator`

The image is built using `livemedia-creator`. `livemedia-creator` uses
[Anaconda](https://github.com/rhinstaller/anaconda),
[kickstart](https://github.com/rhinstaller/pykickstart),
and [Lorax](https://github.com/rhinstaller/lorax) to create a wide range of
outputs, with a focus on flexibility. `livemedia-creator` is used extensively
by many other projects, and it is used here to provide a stable, maintained
way to perform the necessary build and install steps rather than using the
installer tools directly.

The `ovirt-node-ng` repository includes a wrapper around `livemedia-creator`
to simplify usage, and only two arguments need to be provided, with an
optional flag which may be used for development.

Recent versions of Fedora should work, as should other distros (as long as
they're RPM-based, and derived from EL7/F21 or later. Please don't try this
with CentOS 6!), but they probably won't be supported. We'd love to know if
you get it working with another distro, though.

**FIXME** koji support should be added

### Image Format: Liveimg

Node is installed (and updated) using a single operating system image.
Contrary to many other distributions, packages are not used to install the
operating system. Packages are primarily used to [build the image](build.md),
and eventually to [customize the image](impl.md).

The liveimg image format is a Fedora-and-CentOS-ish format used to deliver
LiveCDs. A liveimg is a file-system image wrapped into a squashfs image.
The reasoning behind this Matryoshka mechanism is that the filesystem image
can be mounted easily, and the squashfs image -- as it can compress --
helps reduce the size of the image. Because it has been around for a long time,
this format has mature support in both dracut and anaconda.
This effectively enables two use-cases with a single image:

+   dracut can boot into a liveimg

## Delivery Format

The appliance image is delivered in the squashfs liveimg format.

This format is understood by anaconda (for installation) and dracut (for
stateful and diskless boots).

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

The `ext3fs.img` can be created using a variety of tools, the primary one used
by Node is `livemedia-creator` (part of `lorax`).

[Eventually](https://bugzilla.redhat.com/show_bug.cgi?id=1282496)
`livemedia-creator` will be capable of creating squashfs images directly.
