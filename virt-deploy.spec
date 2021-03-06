%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           virt-deploy
Version:        0.1.5
Release:        1%{?dist}
Summary:        Virtual machines deployment tool

License:        GPLv2
URL:            https://github.com/simon3z/%{name}
Source0:        https://github.com/simon3z/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools

Requires:       python-setuptools
Requires:       python-netaddr
Requires:       libxml2-python
Requires:       qemu-img
Requires:       libguestfs-tools-c
Requires:       virt-install
Requires:       libvirt-daemon-config-network
Requires:       libvirt-daemon-config-nwfilter

%description
Virtual machines deployment tool.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%files
%doc README.md COPYING
%{_bindir}/virt-deploy
%{python_sitelib}/*


%changelog
* Tue Jan 20 2015 Federico Simoncelli <fsimonce@redhat.com> - 0.1.5-1
- update to 0.1.5

* Sat Jan 17 2015 Federico Simoncelli <fsimonce@redhat.com> - 0.1.4-1
- update to 0.1.4

* Thu Jan 15 2015 Federico Simoncelli <fsimonce@redhat.com> - 0.1.3-1
- update to 0.1.3

* Tue Jan 13 2015 Federico Simoncelli <fsimonce@redhat.com> - 0.1.2-1
- update to 0.1.2

* Sat Jan  3 2015 Federico Simoncelli <fsimonce@redhat.com> - 0.1.1-1
- initial build
