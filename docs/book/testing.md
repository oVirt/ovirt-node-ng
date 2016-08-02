# Testing

Continuous Integration is an integral part of Node.
The fact that there is also an Engine appliance is very beneficial.

## Overview

-   Python's unittest infrastructure is used to provide the testing framework
-   All tests are available under */tests*.

To install testing prerequisites, please run:

    sudo yum -y install python-sh

## Node Sanity Testing

The Node image is tested against a basic set of use cases after each build, and
a failure to complete any of these tests should be corrected.

Once you've built an image (see [Getting Started](getting-started.md)), you can


## Integration Testing with oVirt Engine

-   Engine and Node appliances are spawned in distinct, but connected,
(user-session) VMs.

-   virt-install is used to setup the VMs

-   cloud-init is used to do the basic OS configuration (passwords, ssh, and IP
  configuration) Note: cloud-init is not built into the squashfs, it will be
  installed on-demand by the testing infrastructure.

A [reference implementation](
  https://gerrit.ovirt.org/gitweb?p=ovirt-appliance.git;a=tree;f=tests) is part
  of the ovirt-appliance repository.

This setup is very convenient because it provides the following:

-   Environment setup during test suite creation (includes VM creation,
  configuration and initial snapshot)

-   Resetting to the initial snapshot for each testcase

-   SSH to perform in VM operations

-   virsh to control VM lifecycle (reboot, shutdown)
