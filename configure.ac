dnl Copyright (C) 2016-2022 Red Hat, Inc.
dnl
dnl This program is free software; you can redistribute it and/or modify
dnl it under the terms of the GNU General Public License as published by
dnl the Free Software Foundation; version 2 of the License.
dnl
dnl This program is distributed in the hope that it will be useful,
dnl but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
dnl GNU General Public License for more details.
dnl
dnl You should have received a copy of the GNU General Public License
dnl along with this program; if not, write to the Free Software
dnl Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
dnl MA  02110-1301, USA.  A copy of the GNU General Public License is
dnl also available at http://www.gnu.org/copyleft/gpl.html.

define([VERSION_NUMBER], [4.4.3])
define([RELEASEVER], [1])

AC_INIT([ovirt-node-ng], VERSION_NUMBER, [devel@ovirt.org])
AM_INIT_AUTOMAKE([-Wall -Werror foreign -Wno-portability tar-pax no-dist-gzip dist-xz no-dependencies])

PACKAGE_RPM_VERSION="VERSION_NUMBER"
AC_SUBST([PACKAGE_RPM_VERSION])

PACKAGE_RPM_RELEASE="1"
AC_SUBST([PACKAGE_RPM_RELEASE])

AC_SUBST([am__tar], ['find "$$tardir" -print -perm /g=w -exec chmod g-w {} \; | sort | tar --no-recursion --mtime="1970-01-01 00:00Z" --owner=root --group=root -chpf - -T -'])

AC_ARG_WITH([tmpdir],
    [AS_HELP_STRING([--with-tmpdir=DIR],
        [path to TMP directory (default: /tmp)])],
    [TMPDIR="$withval"],
    [TMPDIR="/tmp"])
AC_SUBST([TMPDIR])

AC_ARG_ENABLE(
    [docs],
    [AS_HELP_STRING(
        [--enable-docs],
        [build docs subpackage @<:@default=yes@:>@]
    )],
    ,
    [enable_docs="no"]
)
AS_IF([test "${enable_docs}" = "yes"],
      AC_SUBST([DOCS], ['1']),
      AC_SUBST([DOCS], ['0']))

AC_ARG_ENABLE(
    [tools],
    [AS_HELP_STRING(
        [--enable-tools],
        [build tools subpackage @<:@default=yes@:>@]
    )],
    ,
    [enable_tools="no"]
)
AS_IF([test "${enable_tools}" = "yes"],
      AC_SUBST([TOOLS], ['1']),
      AC_SUBST([TOOLS], ['0']))


AC_ARG_VAR([PEP8], [path to pep8 utility])
AC_CHECK_PROGS([PEP8], [pep8 pycodestyle-3])


AC_CONFIG_FILES([
	Makefile
	src/Makefile
	src/nodectl/config.py
])

AM_PATH_PYTHON([3.6])

AC_OUTPUT
