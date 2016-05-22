################################################################################
#
# systemd-bootchart
#
################################################################################

SYSTEMD_BOOTCHART_VERSION = e6c5e467c4b593114a4cefa17ed10afd6def1d6e
SYSTEMD_BOOTCHART_SITE = https://github.com/systemd/systemd-bootchart.git
SYSTEMD_BOOTCHART_SITE_METHOD = git
SYSTEMD_BOOTCHART_LICENSE = LGPLv2.1+
SYSTEMD_BOOTCHART_DEPENDENCIES = systemd
SYSTEMD_BOOTCHART_AUTORECONF = YES

define SYSTEMD_BOOTCHART_RUN_INTLTOOLIZE
	cd $(@D) && $(HOST_DIR)/usr/bin/intltoolize --force --automake
endef
SYSTEMD_BOOTCHART_PRE_CONFIGURE_HOOKS += SYSTEMD_BOOTCHART_RUN_INTLTOOLIZE

$(eval $(autotools-package))
