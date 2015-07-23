################################################################################
#
# zxing-cpp
#
################################################################################

ZXING_CPP_VERSION = e7594421d240d8a79633a83c7ad3d26b670e038f
ZXING_CPP_SITE = $(call github,glassechidna,zxing-cpp,$(ZXING_CPP_VERSION))
ZXING_CPP_LICENSE = Apache-2.0
ZXING_CPP_LICENSE_FILES = COPYING
ZXING_CPP_INSTALL_STAGING = YES
ZXING_CPP_SUPPORTS_IN_SOURCE_BUILD = NO

ifneq ($(BR2_ENABLE_LOCALE),y)
ifeq ($(BR2_PACKAGE_LIBICONV),y)
ZXING_CPP_DEPENDENCIES += libiconv
endif
endif

define ZXING_CPP_INSTALL_STAGING_CMDS
	for i in $$(find $(@D)/buildroot-build/core/src -iname *.h); do \
		$(INSTALL) -m 644 $$i $(TARGET_DIR)/usr/local/include; \
	done
endef

define ZXING_CPP_INSTALL_TARGET_CMDS
	for i in $$(find $(@D)/buildroot-build/ -iname *.so -o -iname *.a); do \
		$(INSTALL) -m 644 $$i $(TARGET_DIR)/usr/lib; \
	done
	$(INSTALL) -m 755 $(@D)/buildroot-build/zxing $(TARGET_DIR)/usr/sbin
endef

$(eval $(cmake-package))
