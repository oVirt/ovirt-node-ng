#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

"""
During test runs you can watch teh VMs by using virt-manager and looking
at your user sessions:

$ virt-manager -c qemu:///session

Main advantage of this testcase templates:
- Use snapshots to provide clean state per testcase
- Inter-VM communication
- root less (run as a normal user)!
"""

from logging import debug
import unittest
import sh
import os
import tempfile
import time
from virt import DiskImage, VM, CloudConfig
import agent


NODE_IMG = os.environ.get("TEST_NODE_INSTALLED_IMG", None)

ENGINE_IMG = os.environ.get("TEST_ENGINE_ROOTFS_IMG", None)

KEEP_TEST_ENV = bool(os.environ.get("TEST_KEEP_TEST_ENV"))


class TimedoutError(Exception):
    pass


def gen_ssh_identity_file():
    f = os.path.expanduser("~/.ssh/id_rsa")
    if not os.path.exists(f):
        f = tempfile.mkdtemp("testing-ssh") + "/id_rsa"
        sh.ssh_keygen(b=2048, t="rsa", f=f, N="", q=True)
    return f


def check_selinux():
    # FIXME We need permissive mode to work correctly
    SELINUX_ENFORCEMENT_FILE = "/sys/fs/selinux/enforce"
    if os.path.exists(SELINUX_ENFORCEMENT_FILE):
        with open(SELINUX_ENFORCEMENT_FILE, "rt") as src:
            assert "0" == src.read().strip(), \
                   "SELinux is enforcing, but needs to be permissive"


class MachineTestCase(unittest.TestCase):
    """Basic test case to ease VM based testcases

    Just provides a function to create a VM with the relevant
    IP configuration
    """
    @staticmethod
    def _start_vm(name, srcimg, tmpimg, magicnumber, memory_gb=2):
        check_selinux()
        debug("Strating new VM %s" % name)

        ssh_port = 22000 + int(magicnumber)
        ipaddr = "10.11.12.%s" % magicnumber

        img = DiskImage(srcimg).reflink(tmpimg)
        dom = VM.create(name, img, ssh_port=ssh_port, memory_gb=memory_gb)
        dom._ssh_identity_file = gen_ssh_identity_file()

        _fss = dom._fish("run", ":", "list-filesystems")
        if "+1" in _fss:
            # Redefine fish with a layout capable one
            dom.fish = dom.layout_fish
        else:
            raise RuntimeError("No layout found!? %s" % _fss)

        cc = CloudConfig()
        cc.instanceid = name + "-ci"
        cc.password = str(magicnumber)

        # Bring up the second NIC for inter-VM networking
        # cc.runcmd = "ip link set dev eth1 up ; ip addr add {ipaddr}/24 dev
        # eth1".format(ipaddr=ipaddr)
        cc.runcmd = ("nmcli con add con-name bus0 ifname eth1 " +
                     "autoconnect yes type ethernet ip4 {ipaddr}/24 ; " +
                     "nmcli con up id bus0").format(ipaddr=ipaddr)
        cc.runcmd += (" ; grep myhostname /etc/nsswitch.conf || sed " +
                      "-i '/hosts:/ s/$/ myhostname/' /etc/nsswitch.conf")
        with open(dom._ssh_identity_file + ".pub", "rt") as src:
            cc.ssh_authorized_keys = [src.read().strip()]
#        dom.set_cloud_config(cc)

        dom.upload(agent.__file__, "/agent.py")
        dom.post("/etc/systemd/system/multi-user.target.wants/test-agent.service", """
[Unit]
Description=Test Agent
After=local-fs.target

[Service]
Restart=always
ExecStart=/usr/bin/python /agent.py /dev/virtio-ports/local.test.0
""")

        return dom


@unittest.skipUnless(os.path.exists(NODE_IMG), "Node image is missing")
class NodeTestCase(MachineTestCase):
    """Class to do just-Node specific testing

    Mainly this set's up a VM based on the Node appliance image
    and ensures that each testcase runs in a fresh snapshot.
    """
    _img = NODE_IMG
    node = None

    @classmethod
    def setUpClass(cls):
        debug("Using %s image: %s" % (cls, cls._img))
        assert os.path.exists(cls._img)

        try:
            n = "%s-node" % cls.__name__
            cls.node = cls._start_vm(n,
                                     cls._img,
                                     "/tmp/" + n + ".qcow2",
                                     77)

            cls.node.start()
            time.sleep(5)
            cls.snapshot = cls.node.snapshot(remove=False)
        except:
            if cls.node:
                cls.node.undefine()

            raise

    @classmethod
    def tearDownClass(cls):
        if KEEP_TEST_ENV:
            return

        debug("Tearing down %s" % cls)
        if cls.node:
            cls.node.undefine()

    def setUp(self):
        debug("Setting up %s" % self)

    def tearDown(self):
        if self._resultForDoCleanups.failures:
            pass
            # FIXME rescue sos logs

        if KEEP_TEST_ENV:
            return

        debug("Tearing down %s" % self)
        self.snapshot.revert()


class TestNodeTestcase(NodeTestCase):
    """Class to test that the NodeTestCase class works correctly

    To prevent regressions in the lower layer.
    """
    def test_agent_works(self):
        self.node.run("pwd")

    def test_reboot_works(self):
        self.node.run("echo", "We could log in, the host is up")
        self.node.reboot()
        self.node.run("pwd")


if __name__ == "__main__":
    unittest.main()

# vim: et ts=4 sw=4 sts=4
