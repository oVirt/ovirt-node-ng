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
from concurrent import futures
from virt import DiskImage, VM, CloudConfig


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


class MachineTestCase(unittest.TestCase):
    """Basic test case to ease VM based testcases

    Just provides a function to create a VM with the relevant
    IP configuration
    """
    @staticmethod
    def _start_vm(name, srcimg, tmpimg, magicnumber, memory_gb=2):
        # FIXME We need permissive mode to work correctly
        SELINUX_ENFORCEMENT_FILE = "/sys/fs/selinux/enforce"
        if os.path.exists(SELINUX_ENFORCEMENT_FILE):
            with open(SELINUX_ENFORCEMENT_FILE, "rt") as src:
                assert "0" == src.read().strip(), \
                       "SELinux is enforcing, but needs to be permissive"

        debug("Strating new VM %s" % name)

        ssh_port = 22000 + int(magicnumber)
        ipaddr = "10.11.12.%s" % magicnumber

        img = DiskImage(srcimg).reflink(tmpimg)
        dom = VM.create(name, img, ssh_port=ssh_port, memory_gb=memory_gb)
        dom._ssh_identity_file = gen_ssh_identity_file()

        if "+1" in dom._fish("run", ":", "list-filesystems"):
            # Redefine fish with a layout capable one
            dom.fish = dom.layout_fish

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
        dom.set_cloud_config(cc)

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
            cls.node = cls._start_vm(n, cls._img, n + ".qcow2", 77)

            debug("Install cloud-init")
            cls.node.fish("sh", "yum --enablerepo=* "
                          "--setopt=*.skip_if_unavailable=true "
                          "-y "
                          "install sos cloud-init")
            cls.node.fish("sh", "rpm -q cloud-init")

            cls.node.start()
            cls.node.wait_cloud_init_finished()
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
        self.snapshot = self.node.snapshot()

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
    def test_snapshots_work(self):
        """Check if snapshots are working correct
        """
        has_kernel = lambda: "kernel" in self.node.ssh("rpm -q kernel")

        self.assertTrue(has_kernel())

        with self.node.snapshot().context():
            self.node.ssh("rpm -e --nodeps kernel")
            with self.assertRaises(sh.ErrorReturnCode_1):
                has_kernel()

        self.assertTrue(has_kernel())

    def test_ssh_works(self):
        """Check if basic SSH is working correct
        """
        self.node.ssh("pwd")

    def test_shutdown_works(self):
        """Check if host can be shutdown gracefully
        """
        self.node.ssh("echo We could log in, the host is up")
        self.node.shutdown()

    def test_reboot_works(self):
        """Check that a host can be rebooted and comes back
        """
        self.node.ssh("echo We could log in, the host is up")
        self.node.reboot()
        self.node.ssh("pwd")


@unittest.skipUnless(os.path.exists(NODE_IMG), "Node image is missing")
@unittest.skipUnless(os.path.exists(ENGINE_IMG), "Engine image is missing")
class IntegrationTestCase(MachineTestCase):
    node = None
    engine = None

    # FIXME reduce the number of answers to the minimum
    ENGINE_ANSWERS = """
# For master
[environment:default]
OVESETUP_CONFIG/adminPassword=str:password
OVESETUP_CONFIG/fqdn=str:engine.example.com
OVESETUP_ENGINE_CONFIG/fqdn=str:engine.example.com
OVESETUP_VMCONSOLE_PROXY_CONFIG/vmconsoleProxyHost=str:engine.example.com

OVESETUP_AIO/configure=none:None
OVESETUP_AIO/storageDomainName=none:None
OVESETUP_AIO/storageDomainDir=none:None

OVESETUP_APACHE/configureRootRedirection=bool:True
OVESETUP_APACHE/configureSsl=bool:True

OVESETUP_CONFIG/applicationMode=str:both
OVESETUP_CONFIG/remoteEngineSetupStyle=none:None
OVESETUP_CONFIG/storageIsLocal=bool:False
OVESETUP_CONFIG/firewallManager=str:firewalld
OVESETUP_CONFIG/remoteEngineHostRootPassword=none:None
OVESETUP_CONFIG/firewallChangesReview=bool:False
OVESETUP_CONFIG/updateFirewall=bool:True
OVESETUP_CONFIG/remoteEngineHostSshPort=none:None
OVESETUP_CONFIG/storageType=none:None
OVESETUP_CONFIG/engineHeapMax=str:3987M
OVESETUP_CONFIG/isoDomainName=str:ISO_DOMAIN
OVESETUP_CONFIG/isoDomainMountPoint=str:/var/lib/exports/iso
OVESETUP_CONFIG/isoDomainACL=str:*(rw)
OVESETUP_CONFIG/engineHeapMin=str:100M
OVESETUP_CONFIG/websocketProxyConfig=bool:True
OVESETUP_CONFIG/sanWipeAfterDelete=bool:True

OVESETUP_CORE/engineStop=none:None

OVESETUP_DB/database=str:engine
OVESETUP_DB/fixDbViolations=none:None
OVESETUP_DB/secured=bool:False
OVESETUP_DB/host=str:localhost
OVESETUP_DB/user=str:engine
OVESETUP_DB/securedHostValidation=bool:False
OVESETUP_DB/port=int:5432

OVESETUP_DIALOG/confirmSettings=bool:True

OVESETUP_DWH_CORE/enable=bool:False

OVESETUP_ENGINE_CORE/enable=bool:True

OVESETUP_PKI/organization=str:Test

OVESETUP_PROVISIONING/postgresProvisioningEnabled=bool:True

OVESETUP_RHEVM_SUPPORT/configureRedhatSupportPlugin=bool:False

OVESETUP_SYSTEM/memCheckEnabled=bool:False
OVESETUP_SYSTEM/nfsConfigEnabled=bool:False

OVESETUP_VMCONSOLE_PROXY_CONFIG/vmconsoleProxyConfig=bool:True
OVESETUP_VMCONSOLE_PROXY_CONFIG/vmconsoleProxyPort=int:2222

OSETUP_RPMDISTRO/requireRollback=none:None
OSETUP_RPMDISTRO/enableUpgrade=none:None
"""

    @classmethod
    def setUpClass(cls):
        try:
            n = "%s-" % cls.__name__

            cls._node_setup(n)
            cls._engine_setup(n)
        except:
            if cls.node:
                cls.node.undefine()

            if cls.engine:
                cls.engine.undefine()

            raise

    @classmethod
    def tearDownClass(cls):
        if KEEP_TEST_ENV:
            return

        debug("Tearing down %s" % cls)
        if cls.node:
            cls.node.undefine()

        if cls.engine:
            cls.engine.undefine()

    @classmethod
    def _node_setup(cls, n):
        cls.node = cls._start_vm(n + "node", NODE_IMG,
                                 n + "node.qcow2", 77)

        debug("Install cloud-init")
        print(cls.node.fish("sh", "yum --enablerepo=* -y "
                          "--setopt=*.skip_if_unavailable=true "
                      "install sos cloud-init"))

        cls.node.start()
        cls.node.wait_cloud_init_finished()

        debug("Enable fake qemu support")
        cls.node.ssh("yum --enablerepo=ovirt* -y install vdsm-hook-faqemu")
        cls.node.ssh("sed -i '/vars/ a fake_kvm_support = true' "
                     "/etc/vdsm/vdsm.conf")

        # Bug-Url: https://bugzilla.redhat.com/show_bug.cgi?id=1279555
        cls.node.ssh("sed -i '/fake_kvm_support/ s/false/true/' " +
                     "/usr/lib/python2.7/site-packages/vdsm/config.py")

        cls.node_snapshot = cls.node.snapshot()

    @classmethod
    def _engine_setup(cls, n):
        cls.engine = cls._start_vm(n + "engine", ENGINE_IMG,
                                   n + "engine.qcow2", 88,
                                   memory_gb=4)

        debug("Installing engine")

        cls.engine.post("/root/ovirt-engine-answers",
                        cls.ENGINE_ANSWERS)

        # To reduce engines mem requirements
        # cls.engine.post("/etc/ovirt-engine/engine.conf.d/90-mem.conf",
        #                 "ENGINE_PERM_MIN=128m\nENGINE_HEAP_MIN=1g\n")

        cls.engine.start()
        time.sleep(30)
        cls.engine.wait_cloud_init_finished()

        debug("Add static hostname for name resolution")
        cls.engine.ssh("sed -i '/^127.0.0.1/ s/$/ engine.example.com/' "
                       "/etc/hosts")

        #
        # Do the engine setup
        # This assumes that the engine was tested already and
        # this could probably be pulled in a separate testcase
        #
        debug("Run engine setup")
        cls.engine.ssh("engine-setup --offline "
                       "--config-append=/root/ovirt-engine-answers")

        debug("Install sos for log collection")
        cls.engine.ssh("yum install -y sos")
        cls.engine.ssh("yum install -y python-ovirt-engine-sdk4")

        debug("Installation completed")
        cls.engine_snapshot = cls.engine.snapshot()

    def setUp(self):
        debug("Node and Engine are up")

    def tearDown(self):
        if KEEP_TEST_ENV:
            return

        self.node_snapshot.revert()
        self.engine_snapshot.revert()

if __name__ == "__main__":
    unittest.main()

# vim: et ts=4 sw=4 sts=4
