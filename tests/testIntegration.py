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
from testVirt import IntegrationTestCase


NODE_IMG = os.environ.get("TEST_NODE_INSTALLED_IMG", None)

ENGINE_IMG = os.environ.get("TEST_ENGINE_ROOTFS_IMG", None)

KEEP_TEST_ENV = bool(os.environ.get("TEST_KEEP_TEST_ENV"))


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
