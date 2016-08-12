#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# nodectl
#
# Copyright (C) 2016  Red Hat, Inc.
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Ryan Barry <rbarry@redhat.com>
#

import json
import logging

from .utils import LogCapture
from imgbased.plugins.update import rollback
from imgbased.utils import bcolors

log = logging.getLogger()


class Rollback(object):
    """Wraps rolling back imgbased layers. Pretty trivial
    """

    results = dict()

    def __init__(self, app, machine=False, nvr=None):
        self.app = app
        self.machine = machine

        self._do(nvr)

    def _do(self, nvr):
        with LogCapture() as l:
            try:
                dst_layer = rollback(self.app, nvr)
                self.results["success"] = True
                self.results["next_layer"] = str(dst_layer)
            except:
                self.results["success"] = False
                self.results["reason"] = l.getOutput()

    def write(self):
        if self.machine:
            print json.dumps(self.results)
        else:
            # Neither JSON nor YAML gives a very nice output here, so use
            # our own formatter, since pprint includes sigils
            status = bcolors.ok("Success") if self.results["success"] else \
                bcolors.fail("Failure")
            print "Status: %s" % status

            if self.results["success"]:
                print "  New layer: %s" % self.results["next_layer"]
            else:
                print "  Reason:"
                for line in self.results["reason"].splitlines():
                    print "    %s" % line
