# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

pynodectldir = $(pythondir)/nodectl

pynodectl_PYTHON = \
	nodectl/__init__.py \
	nodectl/__main__.py \
	nodectl/banner.py \
	nodectl/info.py \
	nodectl/initialize.py \
	nodectl/motd.py \
	nodectl/status.py \
	nodectl/update.py \
	nodectl/utils.py \
	nodectl/config.py \
	$(NULL)

check-code:
	pyflakes $(wildcard nodectl/*.py)
	$(PEP8) $(wildcard nodectl/*.py)

check: check-code
