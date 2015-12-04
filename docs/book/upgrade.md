# Upgrade & Rollback

**FIXME**

## Overview

**FIXME**

- imgbase for management
- Layout
  - liveimg is rsynced into Thin LV, then made RO and active=n (BASE)
  - Thin snapshot of LV is created, this is RW (LAYER)
  - Boot entry for RW thin snapshot (LAYER) is created

- Upgrade
  - New BASE with new LAYER is created
  - Rsync /etc from old LAYER to new LAYER
  - Set primary boot entry to new LAYER

- Rollback
  - Set primary boot entry to old LAYER


### Assumptions

**FIXME**

- /etc is on LAYER
- /var is on separate volume


### Open Items

- How do driver disks survive an upgrade
- uid drift is solved enough?
- daemon for imgbased
- currentl kernel+initrd in subdir in /boot, idea: keep kernel+initrd in /boot
  this will allow dracut and others to work correct

## Package persistence

**FIXME**

- how - if - should rpms be persisted?
  - separate volume with magic name, put rpm there, will be reinstalled on
    every new layer
  - only through puppet/chef/ansible?
  - yum plugin to record and cache installed pkgs on separate vol?

## Delivery

**FIXME**

- squashfs wrapped in rpm
- "dnf download" rpm on the host
- extract squashfs from the rpm
- then use imgbase to upgrade
