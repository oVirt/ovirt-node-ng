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
from .status import Status
#from . import config

log = logging.getLogger()


class Application(object):
    """Use this application to manage your Node.
    The lify-cycle of a Node starts with the initialization (init).
    This assumes a thin LVM setup, and will perform some operations
    to allow later updates.
    After initializing you can inform (info) yourself about a few
    important facts (build version, ...).
    Over time you can retireve updates (update) if they are available.
    If one update is getting you into a broken state, you can rollback
    (rollback).
    """

    imgbased = None
    machine = False

    def __init__(self):
        self.imgbased = imgbased.Application()

    def init(self, debug):
        """Perform imgbase init
        """
        raise NotImplementedError

    def info(self, debug):
        """Dump metadata and runtime informations

        - metadata
        - storage status
        - bootloader status
        """
        raise NotImplementedError

    def update(self, check, debug):
        """Check for and perform updates
        """
        raise NotImplementedError

    def rollback(self, debug):
        """Rollback to a previous image
        """
        raise NotImplementedError

    def check(self, debug):
        """Check the status of the running system
        """
        from imgbased.plugins.core import Health
        status = Health(self.imgbased).status()

        Status(status, self.machine).write()


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

    root_parser = argparse.ArgumentParser(prog="nodectl",
                                          add_help=False)

    root_parser.add_argument("--version", action="version")
    root_parser.add_argument("--debug", action="store_true")
    root_parser.add_argument("--machine-readable",
                             action="store_true",
                             help="Output in JSON for consumption by other "
                                  "utilities")

    parser = argparse.ArgumentParser(parents=[root_parser],
                                     description=app.__doc__)

    subparsers = parser.add_subparsers(title="Sub-commands", dest="command")

    sp_init = subparsers.add_parser("init",
                                    help="Intialize the required layout")

    sp_info = subparsers.add_parser("info",
                                    help="Show informations about the image")

    sp_update = subparsers.add_parser("update",
                                      help="Perform an update if updates are available")
    sp_update.add_argument("--check", action="store_true")

    sp_rollback = subparsers.add_parser("rollback",
                                        help="Rollback to the previous image")

    sp_info = subparsers.add_parser("check",
                                    help="Show the status of the system")

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
    cmdmap.register("update", app.update)
    cmdmap.register("rollback", app.rollback)
    cmdmap.register("check", app.check)

    return cmdmap.command(args)

# vim: et sts=4 sw=4:
