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
# Refer to the README.md and COPYING files for full details of the license
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
import os
import time
from testVirt import MachineTestCase


NODE_IMG = os.environ.get("TEST_NODE_INSTALLED_IMG", None)

ENGINE_IMG = os.environ.get("TEST_ENGINE_ROOTFS_IMG", None)

KEEP_TEST_ENV = bool(os.environ.get("TEST_KEEP_TEST_ENV"))


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
        cls.node = cls._start_vm(n + "node",
                                 NODE_IMG,
                                 "/var/tmp/" + n + "node.qcow2",
                                 77)

        debug("Install cloud-init")
        print(cls.node.fish("sh", "yum --enablerepo=* -y "
                            "--setopt=*.skip_if_unavailable=true "
                            "install sos cloud-init"))

        cls.node.start()
        cls.node.wait_cloud_init_finished()

        debug("Enable fake qemu support")
        cls.node.run("yum", "--enablerepo=ovirt*", "-y", "install",
                     "vdsm-hook-faqemu")
        cls.node.run("sed", "-i", "-e", "/vars/ a fake_kvm_support = true",
                     "/etc/vdsm/vdsm.conf")

        # Bug-Url: https://bugzilla.redhat.com/show_bug.cgi?id=1279555
        cls.node.run("sed", "-i", "-e", "/fake_kvm_support/ s/false/true/",
                     "/usr/lib/python2.7/site-packages/vdsm/config.py")

        cls.node_snapshot = cls.node.snapshot()

    @classmethod
    def _engine_setup(cls, n):
        cls.engine = cls._start_vm(n + "engine", ENGINE_IMG,
                                   "/var/tmp/" + n + "engine.qcow2", 88,
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
        cls.engine.run("sed", "-i", "-e",
                       "/^127.0.0.1/ s/$/ engine.example.com/",
                       "/etc/hosts")

        #
        # Do the engine setup
        # This assumes that the engine was tested already and
        # this could probably be pulled in a separate testcase
        #
        debug("Run engine setup")
        cls.engine.run("engine-setup", "--offline",
                       "--config-append=/root/ovirt-engine-answers")

        debug("Install sos for log collection")
        cls.engine.run("yum", "install", "-y", "sos")
        cls.engine.run("yum", "install", "-y", "python-ovirt-engine-sdk4")

        debug("Installation completed")
        cls.engine_snapshot = cls.engine.snapshot()

    def setUp(self):
        debug("Node and Engine are up")

    def tearDown(self):
        if KEEP_TEST_ENV:
            return

        self.node_snapshot.revert()
        self.engine_snapshot.revert()


class Test_Tier_0_IntegrationTestCase(IntegrationTestCase):
    def download_sosreport(self):
        debug("Fetching sosreports from Node and Engine")
        self.node.download_sosreport()
        self.engine.download_sosreport()

    def test_tier_1_intra_network_connectivity(self):
        """Check that the basic IP connectivity between VMs is given
        """
        self.node.ssh("ifconfig")
        self.engine.ssh("ifconfig")

        self.node.ssh("arp -n")
        self.engine.ssh("arp -n")

        self.node.ssh("ping -c10 10.11.12.88")
        self.engine.ssh("ping -c10 10.11.12.77")

    def test_tier_1_node_can_reach_engine(self):
        """Check if the node can reach the engine
        """
        self.node.ssh("ping -c3 -i3 10.11.12.88")
        self.engine.ssh("ping -c3 -i3 10.11.12.77")
        self.node.ssh("curl --fail 10.11.12.88 | grep -i engine")

    def test_tier_2_engine_is_up(self):
        """Check that the engine comes up and provides it's API
        """
        self.engine.ssh("curl --fail 127.0.0.1 | grep -i engine")
        # FIXME check connectivity


if __name__ == "__main__":
    unittest.main()

# vim: et ts=4 sw=4 sts=4
