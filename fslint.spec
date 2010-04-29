%define mandriva %([ -f /etc/mandrake-release ] && echo 1 || echo 0)
%define suse %([ -f /etc/SuSE-release ] && echo 1 || echo 0)

Name:           fslint
Version:        2.42
%if %{mandriva}
Release:        1.mdv
%endif
%if %{suse}
Release:        1.suse
%endif
%if !%{mandriva} && !%{suse}
Release:        1
%endif
Summary:        File System "lint" discovery and cleaning utility

Group:          Applications/File
License:        GPL
URL:            http://www.pixelbeat.org/fslint/
Source0:        http://www.pixelbeat.org/fslint/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  gettext >= 0.13, desktop-file-utils

Requires:       python >= 2.3, cpio, findutils
%if %{mandriva}
Requires:       pygtk2.0 >= 2.4, pygtk2.0-libglade
%endif
%if %{suse}
Requires:       python-gtk >= 2.4
%endif
%if !%{mandriva} && !%{suse}
Requires:       pygtk2 >= 2.4, pygtk2-libglade
%endif

%description
FSlint is a utility to find redundant disk usage like duplicate files
for example. It can be used to reclaim disk space and fix other problems
like file naming issues and bad symlinks etc.
It includes a GTK+ GUI as well as a command line interface.


%prep
%setup -q -n %{name}-%{version}
%{__perl} -pi -e 's|^liblocation=.*$|liblocation="%{_datadir}/%{name}" #RPM edit|' fslint-gui
%{__perl} -pi -e 's|^locale_base=.*$|locale_base=None #RPM edit|' fslint-gui


%build
# Not.


%install
rm -rf $RPM_BUILD_ROOT
install -Dpm 755 fslint-gui $RPM_BUILD_ROOT%{_bindir}/fslint-gui
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/%{name}/{fstool,supprt}
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/%{name}/supprt/rmlint
install -dm 755 $RPM_BUILD_ROOT%{_mandir}/man1
install -pm 644 fslint.glade fslint_icon.png \
  $RPM_BUILD_ROOT%{_datadir}/%{name}
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/pixmaps
ln -s ../%{name}/fslint_icon.png $RPM_BUILD_ROOT%{_datadir}/pixmaps
install -pm 755 fslint/{find*,fslint,zipdir} \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint
install -pm 755 fslint/fstool/* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/fstool
install -pm 644 fslint/supprt/fslver \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt
install -pm 755 fslint/supprt/get* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt
install -pm 755 fslint/supprt/md5sum_approx \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt
install -pm 755 fslint/supprt/rmlint/* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt/rmlint

cp -a man/* \
  $RPM_BUILD_ROOT%{_mandir}/man1/

make -C po DESTDIR=$RPM_BUILD_ROOT LOCALEDIR=%{_datadir}/locale install

desktop-file-install \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications \
  --mode 644 \
  %{name}.desktop

%find_lang %{name}


%clean
rm -rf $RPM_BUILD_ROOT


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc doc/*
%{_mandir}/man1/fslint*
%{_bindir}/fslint-gui
%{_datadir}/%{name}
%{_datadir}/applications/*%{name}.desktop
%{_datadir}/pixmaps/fslint_icon.png


%changelog
* Tue Jul 21 2009 Pádraig Brady
- Update GTK+ and Python deps to 2.4 and 2.3 respectively

* Fri Mar 09 2007 Pádraig Brady
- Put more info in description so the package is
  easier to find in repositories

* Wed Nov 01 2006 Pádraig Brady
- Support SuSE
- Removed 0 Epoch to align with fedora policies

* Thu Jun 22 2006 Pádraig Brady
- Added man pages for fslint and fslint-gui
- Support Mandriva
- Other minor cleanups to align with debian package
  (suggested by lintian)

* Mon Jan 02 2006 Pádraig Brady
- /usr/bin/{fs,FS}lint -> /usr/bin/fslint-gui
- Tidy up /usr/bin/fslint/fslint directory

* Mon Aug 16 2004 Pádraig Brady
- Incorporated more packaging changes from fedora

* Mon Sep 01 2003 Pádraig Brady
- Incorporated some packaging changes from fedora

* Tue Jul 08 2003 Pádraig Brady
- Added translation files

* Thu Jan 16 2003 Pádraig Brady
- Changes for gnome2 (redhat 8.x)
- Make install really independent of python version, previously it
  (even though I thought I handled it correctly) assumed the same python
  version as the rpm build machine

* Thu Dec 16 2002 Pádraig Brady
- First incarnation
