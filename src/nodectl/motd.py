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
import os

from imgbased.utils import bcolors

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

log = logging.getLogger()


class Motd(object):
    """A basic wrapper to parse and deal with 'imgbase check'
    """

    def __init__(self, status):
        self.status = json.loads(status)

    def write(self):
        txts = [""]
        if not self.status["status"] == "ok":
            txts += ["  node status: " + bcolors.fail("DEGRADED")]
            txts += ["  Please check the status manually using"
                     " `nodectl check`"]
        else:
            txts += ["  node status: " + bcolors.ok("OK")]
            txts += ["  See `nodectl check` for more information"]
        txts += [""]
        print "\n".join(txts)
