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
# Author(s): Fabian Deutsch <fabiand@redhat.com>
#

import logging
import argparse
import sys

import imgbased

from .banner import Banner
from .motd import Motd
from .info import Info
from .initialize import Initialize
from .update import Rollback
from .status import Status
# from . import config

log = logging.getLogger()


class Application(object):
    """Use this application to manage your Node.
    The life-cycle of a Node starts with the initialization (init).
    This assumes a thin LVM setup, and will perform some operations
    to allow later updates.
    After initializing you can inform (info) yourself about a few
    important facts (build version, ...).
    Over time you can retrieve updates (update) if they are available.
    If one update is getting you into a broken state, you can rollback
    (rollback).
    """

    imgbased = None
    machine = False

    def __init__(self):
        self.imgbased = imgbased.Application()

    def init(self, debug, source, nvr):
        """Perform imgbase init
        """
        Initialize(self.imgbased, self.machine, source, nvr).write()

    def info(self, debug):
        """Dump metadata and runtime informations

        - metadata
        - storage status
        - bootloader status
        """
        # FIXME: we could actually pull a nice object directly out
        # of imgbased, but we'd tie ourselves to the API much too
        # closely. imgbased.naming is directly formatting strings,
        # but we can't instantiate that nicely directly from
        # imgbased.imgbase without making assumptions.
        Info(self.imgbased, self.machine).write()

    def rollback(self, debug, nvr):
        """Rollback to a previous image
        """
        Rollback(self.imgbased, self.machine, nvr).write()

    def banner(self, debug, update_issue):
        """Generate a motd message which shows the IP addresses so
        users know how to get to cockpit. Optionally update /etc/issue
        """
        Banner(update_issue)

    def check(self, debug, oneline):
        """Check the status of the running system
        """
        from imgbased.plugins.core import Health
        status = Health(self.imgbased).status()

        Status(status, self.machine, oneline=oneline).write()

    def motd(self, debug):
        """Check the status of the running system
        """
        from imgbased.plugins.core import Health
        Motd(Status(Health(self.imgbased).status(),
             machine_readable=True).output).write()


class CommandMapper():
    commands = dict()

    def __init__(self):
        self.commands = dict()

    def register(self, command, meth):
        self.commands[command] = meth

    def command(self, args):
        command = args.command
        kwargs = args.__dict__
        del kwargs["command"]
        return self.commands[command](**kwargs)


def CliApplication(args=None):
    app = Application()

    root_parser = argparse.ArgumentParser(add_help=False)

    root_parser.add_argument("--version", action="version")
    root_parser.add_argument("--debug", action="store_true")
    root_parser.add_argument("--machine-readable",
                             action="store_true",
                             help="Output in JSON for consumption by other "
                                  "utilities")

    parser = argparse.ArgumentParser(prog="nodectl",
                                     parents=[root_parser],
                                     description=app.__doc__)

    subparsers = parser.add_subparsers(title="Sub-commands", dest="command")

    subparsers.add_parser("info",
                          help="Show information about the image")

    sp_rollback = subparsers.add_parser("rollback",
                                        help="Rollback a previous image. "
                                        "Defaults to the latest.")
    sp_rollback.add_argument("--nvr",
                             nargs="?",
                             help="A layer nvr to rollback to")

    sp_check = subparsers.add_parser("check",
                                     help="Show the status of the system")

    sp_check.add_argument("--oneline", action="store_true")

    subparsers.add_parser("motd",
                          help="Generate a message to be seen at login")

    sp_init = subparsers.add_parser("init",
                                    help="Initialize an imgbased layout ")

    sp_init.add_argument("--nvr",
                         nargs="?",
                         help="The nvr to initialize as")

    sp_init.add_argument("--source",
                         nargs="?", default="/", metavar="VG/LV",
                         help="An existing thin LV to tag for initialization")

    sp_banner = subparsers.add_parser("generate-banner",
                                      help="Print URLs for system management")

    sp_banner.add_argument("--update-issue",
                           action="store_true",
                           help="Update /etc/issue, which can't use a script")

    (args, remaining_args) = root_parser.parse_known_args()

    if remaining_args:
        args = parser.parse_args(args=remaining_args, namespace=args)
    else:
        parser.print_help()
        sys.exit(1)

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.machine_readable:
        app.machine = True

    # We don't care about passing this to the CommandMapper at all
    del args.machine_readable

    cmdmap = CommandMapper()
    cmdmap.register("init", app.init)
    cmdmap.register("info", app.info)
    cmdmap.register("rollback", app.rollback)
    cmdmap.register("check", app.check)
    cmdmap.register("motd", app.motd)
    cmdmap.register("generate-banner", app.banner)

    return cmdmap.command(args)

# vim: et sts=4 sw=4:
