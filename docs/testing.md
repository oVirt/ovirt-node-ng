# Testing

Continous Integration is an integral part of Node.
The fact that there is also an Engine appliance is very benefitial.

## Overview

- Engine and Node appliance are spawned in distinct but connected
  (user-session) VMs
- virt-install is used to setup the VMs
- cloud-init is used to do the basic OS configuration (passwords, ssh, and IP
  configuration)
- Python's unittest infrastructure is used to provide the testing framework

A [reference implementation](https://gerrit.ovirt.org/gitweb?p=ovirt-appliance.git;a=tree;f=tests)
is part of the ovirt-appliance repository.

This setup is very convenient because it provides the following:

- Environment setup during testsuite creation (includes VM creation,
  configuration and initial snapshot)
- Resetting to the initial snapshot for each testcase
- SSH to perform in VM operations
- virsh to control VM lifecycle (reboot, shutdown)
