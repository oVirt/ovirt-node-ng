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

from logging import debug
import time
import unittest
from testVirt import NodeTestCase


class TestNode(NodeTestCase):
    """Test functionality around imgbase on Node appliance (post-installation)
    """
    #
    # SELinux
    #
    def test_selinux(self):
        assert "Enforcing" in self.node.run("getenforce")

        # data = self.node.run("cat", "/var/log/audit/audit.log")
        # assert "denied" not in data, \
        #     "Denials were found"

    #
    # LVM / Block layer
    #
    def test_lvm(self):
        def lvm(*args):
            return self.node.run("lvm", *args)

        print("Checking if a VG got created")
        vgs = lvm("vgs", "--noheadings").strip().splitlines()
        debug("VGs: %s" % vgs)
        self.assertGreater(len(vgs), 0, "No VGs found")

        print("Checking if LVs with imgbased tags exist")
        tags = ["pool", "init", "base", "layer"]
        for tag in tags:
            lvs = lvm("lvs",
                      "@imgbased:" + tag).strip().splitlines()
            self.assertGreater(len(lvs), 0,
                               "No LV with tag 'imgbased:%s' found." + tag)

    #
    # Bootloader
    #
    def test_bootloader(self):
        print("Checking if boot entries for the layers exist")
        # FIXME this is a pretty rough guess
        assert "+1" in self.node.run("grubby", "--info=ALL")

        print("Checking if directories fr the layers exist")
        # FIXME this is a pretty rough guess
        assert "+1" in self.node.run("find", "/boot")

    #
    # Filesystem, Packages, Mounts, Services
    #
    def test_packages(self):
        req_pkgs = ["vdsm",
                    "cockpit",
                    "imgbased",
                    "cockpit-ovirt-dashboard",
                    "nodectl",
                    "sos"
                    ]

        pkgs = self.node.run("rpm", "-q", *req_pkgs)

        assert len(pkgs) != len(req_pkgs), \
            "Some packages are missing, there are: %s" % pkgs

    def test_mounts(self):
        # Will raise an error if /var is not a mount
        self.node.run("findmnt", "/var")

        self.assertIn("discard",
                      self.node.run("findmnt", "/var"))

        # FIXME
        # self.assertIn("discard",
        #               self.node.run("findmnt", "/"))

    @unittest.skip("FIXME needs a better check")
    def test_services(self):
        req_enabled_units = ["cockpit.socket",
                             "sshd.service",
                             "imgbase-motd.service"
                             ]

        # Give services some time to come up
        # FIXME better to loop
        time.sleep(30)
        self.node.run("systemctl", "is-active",
                      *req_enabled_units)

    #
    # imgbased
    #
    def test_imgbase(self):
        def imgbase(*args):
            return self.node.run("imgbase", *args)

        debug("%s" % imgbase("--version"))

        print("Fix imgbase layout utf-8 output")
        # imgbase("layout")

        print("Checking if w works")
        imgbase("w")

        print("Checking if check passes")
        imgbase("check")

    #
    # cockpit
    #
    def test_cockpit(self):
        debug("Checking if cockpit is reachable")
        html = self.node.run("curl", "--fail", "--insecure",
                             "127.0.0.1:9090")

        debug("Check if the first page is retrieved")
        assert "Cockpit starting" in html


if __name__ == "__main__":
    unittest.main()

# vim: et ts=4 sw=4 sts=4
