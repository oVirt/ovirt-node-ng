# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
import difflib
import sys

import guestfs


def __execute_cmd_squashfs(squashfs_img, cmd_to_exec):
    guest_fs = guestfs.GuestFS(python_return_dict=True)
    guest_fs.add_drive_opts(squashfs_img)
    guest_fs.launch()
    guest_fs.mount_ro("/dev/sda", "/")
    guest_fs.mount_loop("/LiveOS/rootfs.img", "/")

    try:
        ret = guest_fs.command(cmd_to_exec)
    except:
        guest_fs.shutdown()
        return

    guest_fs.shutdown()
    return ret

if __name__ == "__main__":
    rpm = []
    key_pkgs = ['cockpit-ovirt-dashboard', 'kernel',
                'redhat-release-virtualization-host', 'vdsm',
                'ovirt-hosted-engine-setup', 'ovirt-release-master',
                'ovirt-release40']

    if len(sys.argv) != 3:
        print("Generates the manifest file from different squashfs images\n")
        print(("Usage: %s old.squashfs new.squashfs" % sys.argv[0]))
        sys.exit(0)

    kpkgs_header = "Key packages from {0}".format(sys.argv[2])

    print("=" * len(kpkgs_header))
    print(kpkgs_header)
    print("=" * len(kpkgs_header))

    for pkg in key_pkgs:
        ret = __execute_cmd_squashfs(sys.argv[2], ['rpm', '-q', pkg])
        if ret:
            print("* {0}".format(ret.strip()))

    print("=" * len(kpkgs_header))
    print("Diff between images:")
    print("=" * len(kpkgs_header))

    for i in range(1, 3):
        rpm.append(
            __execute_cmd_squashfs(sys.argv[i], ['rpm', '-qa'])
        )

    print(('\n'.join(
          difflib.unified_diff(
              sorted(rpm[0].split()),
              sorted(rpm[1].split()),
              fromfile=sys.argv[1],
              tofile=sys.argv[2]
          ))))
