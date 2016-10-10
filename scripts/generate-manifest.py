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
    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive_opts(squashfs_img)
    g.launch()
    g.mount_ro("/dev/sda", "/")
    g.mount_loop("/LiveOS/rootfs.img", "/")
    ret = g.command(cmd_to_exec)
    g.shutdown()
    return ret

if __name__ == "__main__":
    rpm = []
    key_pkgs = ['rpm', '-q',
                'cockpit-ovirt-dashboard', 'kernel',
                'redhat-release-virtualization-host', 'vdsm',
                'ovirt-hosted-engine-setup']

    if len(sys.argv) != 3:
        print("Generates the manifest file from different squashfs images\n")
        print(("Usage: %s old.squashfs new.squashfs" % sys.argv[0]))
        sys.exit(0)

    print("Key packages in the new image:")
    print("=======================================")
    print("Squashfs: {0}".format(sys.argv[2]))
    print("{0}".format(__execute_cmd_squashfs(sys.argv[2], key_pkgs)))

    print("Diff between images:")
    print("=======================================")
    for i in range(1, 3):
        rpm.append(__execute_cmd_squashfs(sys.argv[i], ['rpm', '-qa']))

    print(('\n'.join(
          difflib.unified_diff(
              sorted(rpm[0].split()),
              sorted(rpm[1].split()),
              fromfile=sys.argv[1],
              tofile=sys.argv[2]
          ))))
