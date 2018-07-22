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

import functools
import logging
import re

from io import StringIO

try:
    string_types = (str, unicode, bytes)
except NameError:
    string_types = (str, bytes)

log = logging.getLogger()


class ContextDecorator(object):
    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwds):
            with self:
                return f(*args, **kwds)
        return decorated


class LogCapture(ContextDecorator):
    def __enter__(self):
        self.buf = StringIO()

        self.oldLogLevel = log.getEffectiveLevel()
        log.setLevel(logging.INFO)

        self.oldLogger = log.handlers[0]
        log.removeHandler(self.oldLogger)

        self.logHandler = logging.StreamHandler(self.buf)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        self.logHandler.setFormatter(formatter)

        log.addHandler(self.logHandler)
        return self

    def __exit__(self, *args):
        # Restore logging level
        log.setLevel(self.oldLogLevel)
        log.removeHandler(self.logHandler)
        log.addHandler(self.oldLogger)

        return False

    def getOutput(self):
        self.logHandler.flush()
        self.buf.flush()

        output = re.sub(r'^\[\w+\]\s+', '', self.buf.getvalue(), flags=re.M)

        return output
