################################################################################
#
# libressl
#
################################################################################

LIBRESSL_VERSION = 2.0.5
LIBRESSL_SITE = http://ftp.openbsd.org/pub/OpenBSD/LibreSSL
LIBRESSL_LICENSE = Apache-1.0, BSD-4c, ISC License, Public Domain
LIBRESSL_INSTALL_STAGING = YES
LIBRESSL_LIBTOOL_PATCH = NO

$(eval $(autotools-package))
