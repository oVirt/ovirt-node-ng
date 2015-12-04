# Filesystem layout and concepts


To especially let upgrades work correctly imgbase is making a few assumptions
about file locations and how the filesystem is organized.
These concepts are well defined by OSTree and the Stateless project from
systemd.

## Overview

A few relevant main points are:

- Only /etc and /var are writable and persisted.
- Vendor presets/configuration goes to /usr/etc
- User configuration goes to /etc
- The user configuration overrides the vendor presets
- Partial configuration snippets can be placed in <conf>.d

The assumption is that these mechanisms above provide enough structure to build
robust upgrades.

**NOTE:** Following these guidelines is one critical point to allow stable
upgrade an rollback.

## Open Items

**FIXME**

- Identify packages which modify config outside of /etc - use imgbase diff
- Patches for other packages to support scheme above,
  like https://gerrit.ovirt.org/#/c/48317/
- Node identifier /etc/os.release.d/50-ovirt-node with VARIANT field
