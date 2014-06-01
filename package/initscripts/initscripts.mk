################################################################################
#
# initscripts
#
################################################################################

# source included in buildroot
INITSCRIPTS_SOURCE =

# Note: We need to override Busybox's inittab with an inittab compatible with
# sysvinit if we want SYSVINIT as our init.
ifeq ($(BR2_PACKAGE_SYSVINIT),y)
define INITSCRIPTS_INSTALL_INITTAB
	$(INSTALL) -D -m 0644 package/initscripts/sysvinit_inittab $(TARGET_DIR)/etc/inittab
endef
else
define INITSCRIPTS_INSTALL_INITTAB
	$(INSTALL) -D -m 0644 package/initscripts/busybox_inittab $(TARGET_DIR)/etc/inittab
endef
endif

define INITSCRIPTS_INSTALL_TARGET_CMDS
	mkdir -p  $(TARGET_DIR)/etc/init.d
	$(INSTALL) -D -m 0755 package/initscripts/init.d/* $(TARGET_DIR)/etc/init.d/
	$(INITSCRIPTS_INSTALL_INITTAB)
endef

$(eval $(generic-package))
