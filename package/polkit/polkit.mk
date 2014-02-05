################################################################################
#
# polkit
#
################################################################################

POLKIT_VERSION = 0.112
POLKIT_SITE = http://www.freedesktop.org/software/polkit/releases/
POLKIT_LICENSE = GPLv2
POLKIT_LICENSE_FILES = COPYING

POLKIT_INSTALL_STAGING = YES

POLKIT_DEPENDENCIES = expat host-intltool host-pkgconf libglib2 spidermonkey

# We could also support --with-authfw=pam
POLKIT_CONF_OPT = \
	--with-authfw=shadow \
	--with-os-type=unknown \
	--disable-man-pages \
	--disable-examples \
	--with-mozjs=mozjs-24

POLKIT_CONF_ENV = \
	PKG_CONFIG_PATH="$(HOST_DIR)/usr/lib/pkgconfig:$(PKG_CONFIG_PATH)"

$(eval $(autotools-package))
