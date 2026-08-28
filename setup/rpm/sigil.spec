%global name sigil
%global unmangled_version %{version}
%global __requires_exclude ^.*sigil/addons/mail/static/scripts/sigil-mailgate.py$

Summary: Sigil Server
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: LGPL-3
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: iantirta.com <info@iantirta.com>
Requires: sassc
BuildRequires: python3-devel
BuildRequires: pyproject-rpm-macros
Url: https://www.iantirta.com

%description
Sigil is a complete ERP and CRM. The main features are accounting (analytic
and financial), stock management, sales and purchases management, tasks
automation, marketing campaigns, help desk, POS, etc. Technical features include
a distributed server, an object database, a dynamic GUI,
customizable reports, and XML-RPC interfaces.

%generate_buildrequires
%pyproject_buildrequires

%prep
%autosetup

%build
%py3_build

%install
%py3_install

%post
#!/bin/sh

set -e

SIGIL_CONFIGURATION_DIR=/etc/sigil
SIGIL_CONFIGURATION_FILE=$SIGIL_CONFIGURATION_DIR/sigil.conf
SIGIL_DATA_DIR=/var/lib/sigil
SIGIL_GROUP="sigil"
SIGIL_LOG_DIR=/var/log/sigil
SIGIL_LOG_FILE=$SIGIL_LOG_DIR/sigil-server.log
SIGIL_USER="sigil"

if ! getent passwd | grep -q "^sigil:"; then
    groupadd $SIGIL_GROUP
    adduser --system --no-create-home $SIGIL_USER -g $SIGIL_GROUP
fi
# Register "$SIGIL_USER" as a postgres user with "Create DB" role attribute
su - postgres -c "createuser -d -R -S $SIGIL_USER" 2> /dev/null || true
# Configuration file
mkdir -p $SIGIL_CONFIGURATION_DIR
# can't copy debian config-file as addons_path is not the same
if [ ! -f $SIGIL_CONFIGURATION_FILE ]
then
    echo "[options]
; This is the password that allows database operations:
; admin_passwd = admin
db_host = False
db_port = False
db_user = $SIGIL_USER
db_password = False
addons_path = %{python3_sitelib}/sigil/addons
default_productivity_apps = True
" > $SIGIL_CONFIGURATION_FILE
    chown $SIGIL_USER:$SIGIL_GROUP $SIGIL_CONFIGURATION_FILE
    chmod 0640 $SIGIL_CONFIGURATION_FILE
fi
# Log
mkdir -p $SIGIL_LOG_DIR
chown $SIGIL_USER:$SIGIL_GROUP $SIGIL_LOG_DIR
chmod 0750 $SIGIL_LOG_DIR
# Data dir
mkdir -p $SIGIL_DATA_DIR
chown $SIGIL_USER:$SIGIL_GROUP $SIGIL_DATA_DIR

INIT_FILE=/lib/systemd/system/sigil.service
touch $INIT_FILE
chmod 0700 $INIT_FILE
cat << EOF > $INIT_FILE
[Unit]
Description=Sigil Open Source ERP and CRM
After=network.target

[Service]
Type=simple
User=sigil
Group=sigil
ExecStart=/usr/bin/sigil --config $SIGIL_CONFIGURATION_FILE --logfile $SIGIL_LOG_FILE
KillMode=mixed

[Install]
WantedBy=multi-user.target
EOF

%files
%{_bindir}/sigil
%{python3_sitelib}/%{name}-*.egg-info
%{python3_sitelib}/%{name}
%pycached %exclude %{python3_sitelib}/doc/cla/stats.py
%pycached %exclude %{python3_sitelib}/setup/*.py
%exclude %{python3_sitelib}/setup/sigil

%changelog
* %{build_date} Christophe Monniez <moc@iantirta.com> - %{version}-%{release}
- Latest updates
