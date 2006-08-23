%define mandriva %([ -f /etc/mandrake-release ] && echo 1 || echo 0)

Name:           fslint
Version:        2.16
%if %{mandriva}
Release:        1.mdk
%else
Release:        1
%endif
Epoch:          0
Summary:        FSlint - a utility to find and clean "lint" on a filesystem

Group:          Applications/File
License:        GPL
URL:            http://www.pixelbeat.org/fslint/
Source0:        http://www.pixelbeat.org/fslint/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  gettext, desktop-file-utils

%if %{mandriva}
Requires:       python >= 0:2.0, pygtk2.0, pygtk2.0-libglade, cpio
%else
Requires:       python >= 0:2.0, pygtk2, pygtk2-libglade, cpio
%endif

%description
FSlint is a toolkit to find all redundant disk usage (duplicate files
for e.g.). It includes a GUI as well as a command line interface.


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
ln -s %{_datadir}/%{name}/fslint_icon.png $RPM_BUILD_ROOT%{_datadir}/pixmaps
install -pm 755 fslint/{find*,fslint,zipdir} \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint
install -pm 755 fslint/fstool/* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/fstool
install -pm 644 fslint/supprt/fslver \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt
install -pm 755 fslint/supprt/get* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt
install -pm 755 fslint/supprt/rmlint/* \
  $RPM_BUILD_ROOT%{_datadir}/%{name}/fslint/supprt/rmlint

cp -a man/* \
  $RPM_BUILD_ROOT%{_mandir}/man1/

make -C po DESTDIR=$RPM_BUILD_ROOT LOCALEDIR=%{_datadir}/locale install

desktop-file-install \
  --vendor author \
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
* Thu Jun 22 2006 Pádraig Brady
- Added man pages for fslint and fslint-gui
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
