# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

PKGROOT		= /opt/stack/bin
ROLLROOT 	= ../../../..
include $(STACKBUILD)/etc/CCRules.mk

build:

install::
	# Install WSGI File
	mkdir -p $(ROOT)/var/www/wsgi
	$(INSTALL) -m 0644 graphql-api.wsgi $(ROOT)/var/www/wsgi/stacki-graphql-api.wsgi

clean::
