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
import re
import subprocess

issue_tmpl = r'''\S
Kernel \r on an \m

'''


class Banner(object):
    """Fetches IP addresses and adds them to motd (on SSH logins)

    Also called on a timer to update /etc/issue
    """

    def __init__(self, machine_readable, update_issue=False):
        self.machine_readable = machine_readable
        self._get_ips()
        self._generate_message()

        if update_issue:
            self.update_issue()
        else:
            self.gen_motd()

    def _get_ips(self):
        output = subprocess.check_output(["ip", "addr"])
        relevant = [l for l in output.splitlines() if "global" in l and
                    "virbr" not in l]

        addresses = []
        for r in relevant:
            addresses.append(re.match(r'inet6?(.*?)/.*',
                                      r.lstrip()).groups()[0].strip())
        self.addresses = addresses

    def _generate_message(self):
        pre = "Admin Console: "
        urls = ' or '.join(["https://%s:9090/" % a for a in self.addresses])

        self._msg = pre + urls

    def gen_motd(self):
        if self.machine_readable:
            msg = dict()
            msg["admin_console"] = self.addresses
            print(json.dumps(msg))
        else:
            print("%s\n" % self._msg)

    def update_issue(self):
        with open('/etc/issue', 'w') as f:
            f.write(issue_tmpl)
            f.write(self._msg)
            f.write('\n\n')
