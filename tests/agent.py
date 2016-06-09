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

import sys
import json
import subprocess
import os
import socket


class Client():
    timeout = 30

    def __init__(self, path):
        self.path = path

    def run(self, *args):
        s = socket.socket(socket.AF_UNIX)
        s.settimeout(self.timeout)
        s.connect(self.path)

        f = s.makefile("a+", bufsize=0)

        data = json.dumps({"args": args})

        print("Writing: %s" % data)

        f.write(data + "\n")

        if args[-1] == "&":
            print("No reply expected")
        else:
            print("Waiting for reply")
            resp = f.readline()
            print("Got reply: %s" % resp)

            j = json.loads(resp)

            if "exception" in j:
                print(resp)
                raise RuntimeError(resp)

            return j["stdout"]


def run(args):
    o = subprocess.check_output
    return o(args,
             stderr=subprocess.STDOUT,
             env={"LC_ALL": "en_US.UTF-8",
                  "PATH": "/bin:/sbin:/usr/bin:/usr/sbin"})


def main():
    f = sys.argv[1]
    assert os.path.exists(f)

    with open(f, "w+") as f:
        while True:
            resp = {}
            try:
                line = f.readline().strip()

                if not line:
                    continue
                print("read: " + line)
                vec = json.loads(line)

                assert "args" in vec
                stdout = run(vec["args"])
                resp["returncode"] = 0
                resp["stdout"] = stdout

            except subprocess.CalledProcessError as e:
                print(e, repr(e))
                resp["exception"] = str(e)
                resp["stdout"] = e.output

            except Exception as e:
                print(e, repr(e))
                resp["exception"] = str(e)

            print("resp: " + str(resp))
            f.write(json.dumps(resp) + "\n")


if __name__ == "__main__":
    main()

# vim: et ts=4 sw=4 sts=4
