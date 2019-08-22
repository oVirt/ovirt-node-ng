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
import re
import sys

from imgbased.bootloader import BootConfiguration

from .utils import string_types

log = logging.getLogger()


class Info(object):
    """Fetches and displays some information about the running node:

    Bootloader information
    Layout information
    """

    results = dict()

    def __init__(self, app, machine=False):
        self.app = app
        self.machine = machine
        self._fetch_information()

    def _fetch_information(self):
        self._get_bootloader_info()
        self._get_layout()

    def _get_bootloader_info(self):
        b = BootConfiguration()
        bootinfo = dict()

        bootinfo["default"] = b.get_default()
        bootinfo["entries"] = dict()
        for k, v in b.list().items():
            # FIXME: this isn't very nice. GrubbyEntry should present
            # a clean way for a dict which can be JSON serializable.
            # json chokes with __repr__, so maybe a custom decoder?
            for entry in v:
                bootinfo["entries"][entry.title] = entry.__dict__

        self.results["bootloader"] = bootinfo

    def _get_layout(self):
        layout = LayoutParser(self.app.imgbase.layout()).parse()
        self.results["layers"] = layout
        self.results["current_layer"] = \
            str(self.app.imgbase.current_layer())

    def write(self):
        def pretty_print(k, indent=0):
            sys.stdout.write('{0}{1}: '.format(' ' * indent, k[0]))
            if isinstance(k[1], string_types):
                sys.stdout.write('{0}\n'.format(k[1]))

            elif isinstance(k[1], dict):
                sys.stdout.write('\n')
                items = list(k[1].items())
                if k[0] == "entries":  # bootloader entries
                    items.sort(key=lambda x: x[1]["index"])
                for item in items:
                    pretty_print(item, indent+2)

            elif isinstance(k[1], list):
                sys.stdout.write('\n')
                for item in k[1]:
                    print('{0}{1}'.format(' ' * (indent + 2), item))

            sys.stdout.flush()

        if self.machine:
            print(json.dumps(self.results))
        else:
            # Neither JSON nor YAML gives a very nice output here, so use
            # our own formatter, since pprint includes sigils
            for k in self.results.items():
                pretty_print(k)


class LayoutParser(object):
    """This parser grabs the output of "imgbase layout" and turns it into
    something which is easily consumable by regular Python (until imgbased
    itself can get some tweaking to make this better
    """

    layout = None

    def __init__(self, layout):
        self.layout = layout

    def parse(self):
        result = dict()
        layouts = re.split(r'\n?(?=\w)', self.layout, re.M)

        for l in layouts:
            lines = l.splitlines()
            parent = lines.pop(0)
            result[parent] = []
            for line in lines:
                line = re.sub(r'^.*?(\w+)', r'\1', line)
                result[parent].append(line)

        return result
