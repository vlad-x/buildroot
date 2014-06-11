################################################################################
#
# eudev
#
################################################################################

EUDEV_VERSION = 1.9
EUDEV_SOURCE = eudev-$(EUDEV_VERSION).tar.gz
EUDEV_SITE = http://dev.gentoo.org/~blueness/eudev
EUDEV_LICENSE = GPLv2+ (programs), LGPLv2.1+ (libraries)
EUDEV_LICENSE_FILES = COPYING
EUDEV_INSTALL_STAGING = YES

# mq_getattr is in librt
EUDEV_CONF_ENV += LIBS=-lrt

EUDEV_CONF_OPT =		\
	--disable-manpages	\
	--with-rootlibdir=/lib	\
	--libexecdir=/lib	\
	--with-firmware-path=/lib/firmware	\
	--disable-introspection			\
	--enable-split-usr

EUDEV_DEPENDENCIES = host-pkgconf
EUDEV_PROVIDES = libudev

ifeq ($(BR2_PACKAGE_EUDEV_DAEMON),y)

EUDEV_DEPENDENCIES += host-gperf util-linux kmod
EUDEV_PROVIDES += udev

EUDEV_CONF_OPT += \
	--sbindir=/sbin \
	--enable-libkmod

ifeq ($(BR2_PACKAGE_EUDEV_RULES_GEN),y)
EUDEV_CONF_OPT += --enable-rule_generator
else
EUDEV_CONF_OPT += --disable-rule_generator
endif

ifeq ($(BR2_PACKAGE_LIBGLIB2),y)
EUDEV_CONF_OPT += --enable-gudev
EUDEV_DEPENDENCIES += libglib2
else
EUDEV_CONF_OPT += --disable-gudev
endif

define EUDEV_INSTALL_INIT_SYSV
	$(INSTALL) -m 0755 package/eudev/S10udev $(TARGET_DIR)/etc/init.d/S10udev
endef

else # ! daemon

EUDEV_CONF_OPT += \
	--disable-keymap \
	--disable-libkmod \
	--disable-modules \
	--disable-selinux \
	--disable-rule-generator \
	--disable-gtk-doc \
	--disable-gudev

# When not installing the daemon, we have to override the build and install
# commands, to just install the library.

define EUDEV_BUILD_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D)/src/libudev
endef

# Symlink udev.pc to libudev.pc for those packages that conflate the two
# and 'Requires: udev' when they should just 'Requires: libudev'. Do the
# symlink, to avoid patching each and all of those packages.
define EUDEV_INSTALL_STAGING_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D)/src/libudev DESTDIR=$(STAGING_DIR) install
	ln -sf libudev.pc $(STAGING_DIR)/usr/lib/pkgconfig/udev.pc
endef

define EUDEV_INSTALL_TARGET_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D)/src/libudev DESTDIR=$(TARGET_DIR) install
endef

endif # ! daemon

$(eval $(autotools-package))
