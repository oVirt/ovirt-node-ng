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
from imgbased.utils import bcolors
from imgbased.plugins.core import Layout

log = logging.getLogger()


class Initialize(object):
    """Wraps rolling back imgbased layers. Pretty trivial
    """

    results = dict()

    def __init__(self, app, machine, source, nvr):
        self.app = app
        self.machine = machine

        self._do(source, nvr)

    def _do(self, source, nvr):
        with LogCapture() as log:
            try:
                layout = Layout(self.app)
                layout.initialize(source, nvr)
                success = True
            except (Layout.NVRRequiredError,
                    Layout.InitializationFailedError) as e:
                success = False
                self.results["reason"] = str(e)
            except Exception:
                # Failure -- an exceptionw was thrown from somewhere inside the
                # imgbased hook emitting
                success = False
                self.results["reason"] = log.getOutput()

            self.results["success"] = success

    def write(self):
        if self.machine:
            print(json.dumps(self.results))
        else:
            # Neither JSON nor YAML gives a very nice output here, so use
            # our own formatter, since pprint includes sigils
            status = bcolors.ok("Success") if self.results["success"] else \
                bcolors.fail("Failure")
            print("Status: %s" % status)

            if self.results["success"]:
                print("  Please reboot to use the initialized system")
            else:
                print("  Reason:")
                for line in self.results["reason"].splitlines():
                    print("    %s" % line)
