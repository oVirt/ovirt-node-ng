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
import re
import subprocess

from imgbased.utils import bcolors

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

log = logging.getLogger()


class Status(object):
    """A basic wrapper to parse and deal with 'imgbase check'
    """

    machine = None
    output = None

    def __init__(self, status, machine_readable=False, oneline=False):
        self.machine_readable = machine_readable
        self.oneline = oneline

        self._update_info(status)

    def _update_info(self, status):
        services = {"vdsmd": VdsmStatus}
        statuses = {}

        for service, checker in services.iteritems():
            srv_status = checker(service)
            srv_machine = StatusParser(srv_status).parse()
            vals = {"human": srv_status,
                    "machine": srv_machine,
                    "status": srv_machine[service]["status"]
                    }

            statuses[service] = vals

        if self.machine_readable:
            output = dict()

            output.update(StatusParser(status.results).parse())
            for k, v in statuses.items():
                service_status = v["machine"]
                if v["status"] != "ok":
                    output["status"] = "warn"
                output.update(service_status)

            overall_status = str(status)
            if "ok" not in status.lower():
                output.update({"status": "bad"})

            self.output = json.dumps(output)

        else:
            output = status.details().splitlines()

            overall_status = output.pop(0)

            for k, v in statuses.items():
                if v["status"] != "ok":
                    fields = overall_status.split()
                    overall_status = "%s %s" % (fields[0],
                                                bcolors.warn("WARN"))
                output.append(v["human"])

            output = "%s\n%s" % (overall_status, '\n'.join(output))
            self.output = output

    def write(self):
        if self.oneline:
            self.write_motd()
        else:
            print self.output

    def write_motd(self):
        print "\n  Node {0}\n".format(
                re.sub(r'\033\[1m', '', self.output.split('\n')[0]))


class StatusParser(object):
    """This parser grabs the output of "imgbased check" and turns it into
    something which is easily consumable by regular Python (until imgbased
    itself can get some tweaking to make this better

    It could easily be a function for now, but keep it as a class for when
    imgbased gets a better API
    """

    status = None
    mapper = re.compile(r'(?P<test>.*?)(?:(:|\s+\.+\s+))(?P<status>.*)')

    def __init__(self, status):
        self.status = status

    def parse(self):
        if isinstance(self.status, basestring):
            cat, result = self.parse_line(self.status)
            return {cat: result}
        else:
            results = dict()

            for s in self.status:
                results["status"] = "ok" if s.is_ok() else "bad"
                d = [self.strip_ansi(l) for l in s.details().splitlines()]
                cat, result = self.parse_line(d.pop(0))

                results[cat] = result

                for l in d:
                    v, r = self.parse_line(l)
                    results[cat][v] = r

        return results

    def convert_machine(self, item):
        item = re.sub(r'^\s+', '', item)
        item = re.sub(r'\s', '_', item)
        item = re.sub(r'/', '', item)
        return item

    def strip_ansi(self, line):
        line = re.sub(r'\x1b\[[0-9;]*[mG]', '', line)
        return line

    def parse_line(self, line):
        line = line.lower()
        m = self.mapper.match(self.strip_ansi(line))

        cat = self.convert_machine(m.group('test'))
        return (cat, {"status": m.group('status')})


class ServiceStatus(object):
    """A small wrapper to fetch and return the output of services
    """

    def __new__(self, service):
        tmpl = '{0} ... {1}'
        try:
            subprocess.check_call(["systemctl", "status", "%s.service" %
                                   service], stdout=DEVNULL,
                                  stderr=DEVNULL)
            return tmpl.format(service, bcolors.ok("OK"))
        except Exception:
            return tmpl.format(service, bcolors.fail("BAD"))


class VdsmStatus(object):
    """
    Handle vdsm specially, since it may never have been started
    after an install, but we don't want to flag it as bad in this
    case
    """

    def __new__(self, service):
        tmpl = '{0} ... {1}'
        try:
            subprocess.check_call(["systemctl", "status", "%s.service" %
                                   service], stdout=DEVNULL,
                                  stderr=DEVNULL)
            return tmpl.format(service, bcolors.ok("OK"))
        except Exception:
            log = subprocess.check_output(["journalctl", "-u",
                                           "vdsmd.service"])

            has_run = False
            for line in log.splitlines():
                if "Started" in line:
                    has_run = True

            if has_run:
                return tmpl.format(service, bcolors.fail("BAD"))
            else:
                return tmpl.format(service, bcolors.ok("OK"))
