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

from __future__ import absolute_import

import errno
import types
import unittest

from mock import MagicMock
from mock import patch

libvirt_mock = types.ModuleType('libvirt')

libvirt_mock.VIR_NETWORK_UPDATE_COMMAND_ADD_LAST = 3
libvirt_mock.VIR_NETWORK_UPDATE_COMMAND_DELETE = 2
libvirt_mock.VIR_NETWORK_UPDATE_COMMAND_MODIFY = 1
libvirt_mock.VIR_NETWORK_SECTION_DNS_HOST = 10
libvirt_mock.VIR_NETWORK_SECTION_IP_DHCP_HOST = 4
libvirt_mock.VIR_NETWORK_UPDATE_AFFECT_CONFIG = 2
libvirt_mock.VIR_NETWORK_UPDATE_AFFECT_LIVE = 1
libvirt_mock.VIR_ERR_OPERATION_INVALID = 55


class libvirtErrorMock(Exception):
    def __init__(self, code):
        self.code = code

    def get_error_code(self):
        return self.code

libvirt_mock.libvirtError = libvirtErrorMock

_driver = None


def driver():
    global _driver

    if _driver is None:
        with patch.dict('sys.modules', {'libvirt': libvirt_mock}):
            _driver = __import__('libvirt', globals(), locals(),
                                 ['libvirt'], 1)

    return _driver


def XMLDescMock(xmldesc=None):
    return MagicMock(**{'XMLDesc.return_value': xmldesc})


class TestImageOS(unittest.TestCase):
    def test_get_image_os(self):
        image_oses = (
            ('centos-6', 'centos6.5'),
            ('centos-7.0', 'centos7.0'),
            ('fedora-18', 'fedora18'),
            ('fedora-19', 'fedora19'),
            ('fedora-20', 'fedora20'),
            ('fedora-21', 'fedora21'),
        )

        for image, os in image_oses:
            assert os == driver()._get_image_os(image)


class TestNetwork(unittest.TestCase):
    NETXML_DOMAIN = """\
<network>
  <domain name='mydomain.example.com'/>
</network>
"""

    NETXML_DOMAIN_EMPTY = """\
<network>
  <domain/>
</network>
"""

    NETXML_DOMAIN_MISSING = """\
<network>
  <domain/>
</network>
"""

    def test_network_name(self):
        net = XMLDescMock(self.NETXML_DOMAIN)

        name = driver()._get_network_domainname(net)

        net.XMLDesc.assert_called_with()
        assert name == 'mydomain.example.com'

    def test_network_name_empty(self):
        net = XMLDescMock(self.NETXML_DOMAIN_EMPTY)

        name = driver()._get_network_domainname(net)

        net.XMLDesc.assert_called_with()
        assert name is None

    def test_network_name_missing(self):
        net = XMLDescMock(self.NETXML_DOMAIN_MISSING)

        name = driver()._get_network_domainname(net)

        net.XMLDesc.assert_called_with()
        assert name is None


class TestStorage(unittest.TestCase):
    POOLXML_PATH_DIR = """\
<pool type='dir'>
  <target>
    <path>/var/lib/libvirt/images</path>
  </target>
</pool>
"""

    POOLXML_PATH_ISCSI = """\
<pool type='iscsi'>
  <target>
    <path>/var/lib/libvirt/images</path>
  </target>
</pool>
"""

    def test_pool_path_dir(self):
        pool = XMLDescMock(self.POOLXML_PATH_DIR)

        path = driver()._get_pool_path(pool)

        pool.XMLDesc.assert_called_with()
        assert path == '/var/lib/libvirt/images'

    def test_pool_path_iscsi(self):
        pool = XMLDescMock(self.POOLXML_PATH_ISCSI)

        with self.assertRaises(OSError) as cm:
            driver()._get_pool_path(pool)

        assert cm.exception.errno == errno.ENOENT


class TestDomain(unittest.TestCase):
    DOMXML_ONE_MACADDR = """\
<domain type='kvm'>
  <devices>
    <interface type='network'>
      <mac address='52:54:00:a0:b0:01'/>
      <source network='default'/>
    </interface>
  </devices>
</domain>
"""

    DOMXML_MULTI_MACADDR = """\
<domain type='kvm'>
  <devices>
    <interface type='network'>
      <mac address='52:54:00:a0:b0:01'/>
      <source network='default'/>
    </interface>
    <interface type='network'>
      <mac address='52:54:00:a0:b0:02'/>
      <source network='default'/>
    </interface>
    <interface type='network'>
      <mac address='52:54:00:a0:b0:03'/>
      <source network='othernet1'/>
    </interface>
  </devices>
</domain>
"""

    def test_get_domain_one_mac_addresses(self):
        domain = XMLDescMock(self.DOMXML_ONE_MACADDR)

        macs = list(driver()._get_domain_mac_addresses(domain))

        domain.XMLDesc.assert_called_with()
        assert macs == [
            {'mac': '52:54:00:a0:b0:01', 'network': 'default'},
        ]

    def test_get_domain_multi_mac_addresses(self):
        domain = XMLDescMock(self.DOMXML_MULTI_MACADDR)

        macs = list(driver()._get_domain_mac_addresses(domain))

        domain.XMLDesc.assert_called_with()
        assert macs == [
            {'mac': '52:54:00:a0:b0:01', 'network': 'default'},
            {'mac': '52:54:00:a0:b0:02', 'network': 'default'},
            {'mac': '52:54:00:a0:b0:03', 'network': 'othernet1'},
        ]


class TestNetworkDhcpHosts(unittest.TestCase):
    NETXML_DHCP = """\
<network>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <host mac='52:54:00:a1:b2:01' name='test01' ip='192.168.122.2'/>
      <host mac='52:54:00:a1:b2:02' name='test02' ip='192.168.122.3'/>
      <host mac='52:54:00:a1:b2:03' ip='192.168.122.4'/>
    </dhcp>
  </ip>
</network>
"""

    NETXML_DHCP_EXPECTED = [
        {'mac': '52:54:00:a1:b2:01', 'name': 'test01',
         'ip': '192.168.122.2'},
        {'mac': '52:54:00:a1:b2:02', 'name': 'test02',
         'ip': '192.168.122.3'},
        {'mac': '52:54:00:a1:b2:03', 'name': None,
         'ip': '192.168.122.4'},
    ]

    NETXML_LEASES = [
        {'hostname': 'lease04', 'mac': '52:54:00:a1:b2:01',
         'ipaddr': '192.168.122.5'},
        {'hostname': 'lease05', 'mac': '52:54:00:a1:b2:02',
         'ipaddr': '192.168.122.6'},
        {'hostname': None, 'mac': '52:54:00:a1:b2:03',
         'ipaddr': '192.168.122.7'},
    ]

    NETXML_LEASES_EXPECTED = [
        {'mac': '52:54:00:a1:b2:01', 'name': 'lease04',
         'ip': '192.168.122.5'},
        {'mac': '52:54:00:a1:b2:02', 'name': 'lease05',
         'ip': '192.168.122.6'},
        {'mac': '52:54:00:a1:b2:03', 'name': None,
         'ip': '192.168.122.7'},
    ]

    NETXML_DHCP_EMPTY = """\
<network>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp/>
  </ip>
</network>
"""

    NETXML_DHCP_MISSING = """\
<network>
  <ip address='192.168.122.1' netmask='255.255.255.0'/>
</network>
"""

    def test_dhcp_hosts(self):
        net = XMLDescMock(self.NETXML_DHCP)

        hosts = list(driver()._get_network_dhcp_hosts(net))

        net.XMLDesc.assert_called_with()
        assert hosts == self.NETXML_DHCP_EXPECTED

    def test_dhcp_hosts_empty(self):
        net = XMLDescMock(self.NETXML_DHCP_EMPTY)

        hosts = list(driver()._get_network_dhcp_hosts(net))

        net.XMLDesc.assert_called_with()
        assert hosts == list()

    def test_dhcp_hosts_missing(self):
        net = XMLDescMock(self.NETXML_DHCP_MISSING)

        hosts = list(driver()._get_network_dhcp_hosts(net))

        net.XMLDesc.assert_called_with()
        assert hosts == list()

    def test_add_dhcp_host(self):
        net = MagicMock()

        driver()._add_network_dhcp_host(net, 'test01', '52:54:00:a1:b2:01',
                                        '192.168.122.2')

        expected_xml = ('<host mac="52:54:00:a1:b2:01" name="test01" '
                        'ip="192.168.122.2"/>')
        net.update.assert_called_with(3, 4, 0, expected_xml.encode(), 3)

    def test_del_dhcp_host(self):
        net = MagicMock()

        driver()._del_network_dhcp_host(net, '192.168.122.2')

        expected_xml = '<host ip="192.168.122.2"/>'
        net.update.assert_called_with(2, 4, 0, expected_xml.encode(), 3)

    def test_del_dhcp_host_failure_raised(self):
        net = MagicMock()
        net.update.side_effect = libvirtErrorMock(1)

        with self.assertRaises(libvirtErrorMock):
            driver()._del_network_dhcp_host(net, '192.168.122.2')

    def test_del_dhcp_host_failure_caught(self):
        net = MagicMock()
        net.update.side_effect = libvirtErrorMock(55)
        driver()._del_network_dhcp_host(net, '192.168.122.2')

    def test_get_dhcp_leases(self):
        net = XMLDescMock(self.NETXML_DHCP)
        net.DHCPLeases.return_value = self.NETXML_LEASES

        hosts = list(driver()._get_network_dhcp_leases(net))

        net.DHCPLeases.assert_called_with()
        assert hosts == (self.NETXML_DHCP_EXPECTED +
                         self.NETXML_LEASES_EXPECTED)

    def test_new_network_ipaddress(self):
        net = XMLDescMock(self.NETXML_DHCP)
        net.DHCPLeases.return_value = self.NETXML_LEASES

        ipaddress = driver()._new_network_ipaddress(net)

        assert ipaddress == '192.168.122.8'


class TestNetworkDnsHosts(unittest.TestCase):
    def test_add_dns_host(self):
        net = MagicMock()

        driver()._add_network_host(net, 'test01', '192.168.122.2')

        expected_xml = ('<host ip="192.168.122.2">'
                        '<hostname>test01</hostname></host>')
        net.update.assert_called_with(3, 10, 0, expected_xml.encode(), 3)

    def test_del_dns_host(self):
        net = MagicMock()

        driver()._del_network_host(net, '192.168.122.2')

        expected_xml = '<host ip="192.168.122.2"/>'
        net.update.assert_called_with(2, 10, 0, expected_xml.encode(), 3)

    def test_del_dns_failure_raised(self):
        net = MagicMock()
        net.update.side_effect = libvirtErrorMock(1)

        with self.assertRaises(libvirtErrorMock):
            driver()._del_network_host(net, '192.168.122.2')

    def test_del_dns_failure_caught(self):
        net = MagicMock()
        net.update.side_effect = libvirtErrorMock(55)

        driver()._del_network_host(net, '192.168.122.2')
