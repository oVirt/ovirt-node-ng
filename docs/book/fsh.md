# Filesystem layout and concepts


`imgbased` makes a few assumptions about file locations and how the filesystem
is organized in order to make upgrades work correctly
These concepts have been clearly defined by OSTree, and the Stateless project
from systemd.

## Overview

A few relevant points are:

- Only /etc and /var are writable and persisted.
- Vendor presets/configuration goes to /usr/etc
- User configuration goes to /etc
- User configuration overrides the vendor presets
- Partial configuration snippets can be placed in <conf>.d

The assumption is that these mechanisms provide enough structure to build
robust upgrades.

**NOTE:** Following these guidelines is one critical point to allow stable
upgrade and rollback.

## Open Items

**FIXME**

- Identify packages which modify config outside of /etc - use imgbase diff
- Patches for other packages to support the above schema,
  like https://gerrit.ovirt.org/#/c/48317/
- Node identifier /etc/os.release.d/50-ovirt-node with VARIANT field
