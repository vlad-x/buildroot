################################################################################
#
# libconnman-qt
#
################################################################################

LIBCONNMAN_QT_VERSION = 1.0.65
LIBCONNMAN_QT_SITE = $(call github,nemomobile,libconnman-qt,$(LIBCONNMAN_QT_VERSION))
LIBCONNMAN_QT_LICENSE = MIT
LIBCONNMAN_QT_INSTALL_STAGING = YES

ifeq ($(BR2_PACKAGE_QT5), y)
LIBCONNMAN_QT_DEPENDENCIES = qt5base
endif

ifeq ($(BR2_PACKAGE_QT), y)
LIBCONNMAN_QT_DEPENDENCIES = qt
endif

define LIBCONNMAN_QT_CONFIGURE_CMDS
	(cd $(@D); $(HOST_DIR)/usr/bin/qmake)
endef

define LIBCONNMAN_QT_BUILD_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D)
endef

define LIBCONNMAN_QT_INSTALL_STAGING_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D) INSTALL_ROOT=$(STAGING_DIR) install
endef

define LIBCONNMAN_QT_INSTALL_TARGET_CMDS
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D) INSTALL_ROOT=$(TARGET_DIR) install
endef

$(eval $(generic-package))
