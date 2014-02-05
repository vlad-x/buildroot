################################################################################
#
# spidermonkey
#
################################################################################

SPIDERMONKEY_VERSION = 24.2.0
SPIDERMONKEY_SOURCE = mozjs-$(SPIDERMONKEY_VERSION).tar.bz2
SPIDERMONKEY_SITE = http://ftp.mozilla.org/pub/mozilla.org/js/
SPIDERMONKEY_SUBDIR = js/src
SPIDERMONKEY_INSTALL_STAGING = YES
SPIDERMONKEY_LICENSE = MPL-2.0
SPIDERMONKEY_LICENSE_FILES = COPYING
SPIDERMONKEY_DEPENDENCIES += libnspr host-spidermonkey

SPIDERMONKEY_MAKE_OPT = INSTALL="$(HOST_DIR)/usr/bin/nsinstall" \
						NSINSTALL="$(HOST_DIR)/usr/bin/nsinstall"

SPIDERMONKEY_INSTALL_STAGING_OPT = INSTALL="$(HOST_DIR)/usr/bin/nsinstall" \
								   NSINSTALL="$(HOST_DIR)/usr/bin/nsinstall"

SPIDERMONKEY_INSTALL_TARGET_OPT = INSTALL="$(HOST_DIR)/usr/bin/nsinstall" \
								  NSINSTALL="$(HOST_DIR)/usr/bin/nsinstall"

define HOST_SPIDERMONKEY_BUILD_CMDS
	$(HOSTCC) $(@D)/js/src/config/nsinstall.c $(@D)/js/src/config/pathsub.c -o $(@D)/js/src/config/nsinstall
	$(HOSTCXX) -I$(@D)/js/src $(@D)/js/src/jskwgen.cpp -o $(@D)/js/src/host_jskwgen
	$(HOSTCXX) $(@D)/js/src/jsoplengen.cpp -o $(@D)/js/src/host_jsoplengen
endef

define HOST_SPIDERMONKEY_INSTALL_CMDS
	$(INSTALL) -m 0755 -D $(@D)/js/src/config/nsinstall $(HOST_DIR)/usr/bin/nsinstall
	$(INSTALL) -m 0755 -D $(@D)/js/src/host_jskwgen $(HOST_DIR)/usr/bin/host_jskwgen
	$(INSTALL) -m 0755 -D $(@D)/js/src/host_jsoplengen $(HOST_DIR)/usr/bin/host_jsoplengen
endef

$(eval $(autotools-package))
$(eval $(host-generic-package))
