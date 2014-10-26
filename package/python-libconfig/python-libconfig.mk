################################################################################
#
# python-libconfig
#
################################################################################

PYTHON_LIBCONFIG_VERSION = 2f0c9803c98871ff28144f6001442ddcb2762933
PYTHON_LIBCONFIG_SITE = $(call github,cnangel,python-libconfig,$(PYTHON_LIBCONFIG_VERSION))
PYTHON_LIBCONFIG_LICENSE = BSD
PYTHON_LIBCONFIG_LICENSE_FILES = README
PYTHON_LIBCONFIG_SETUP_TYPE = setuptools
PYTHON_LIBCONFIG_DEPENDENCIES = libconfig boost

define PYTHON_LIBCONFIG_BUILD_CMDS
    (cd $(@D); \
        $(PKG_PYTHON_SETUPTOOLS_ENV) \
        $(HOST_DIR)/usr/bin/python setup.py build_ext \
            --boostpython=$(STAGING_DIR)/usr)
endef

$(eval $(python-package))
