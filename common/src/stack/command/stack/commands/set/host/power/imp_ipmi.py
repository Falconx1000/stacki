# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import shlex
from stack.util import _exec
from stack.exception import CommandError
from stack import api

class Implementation(stack.commands.Implementation):
	def run(self, args):
		host = args[0]
		cmd = args[1]
		ipmi_ip = ''
		username = ''
		password = ''

		for interface in api.Call('list.host.interface', args = [host]):
			if interface['interface'] == 'ipmi':
				ipmi_ip = interface['ip']
		if not ipmi_ip:
			raise CommandError(self, f'{host} missing ipmi interface.')

		username = api.Call('list.host.attr', args = [host, 'attr=ipmi_username'])
		if not username:
			username = 'root'

		password = api.Call('list.host.attr', args = [host, 'attr=ipmi_password'])[0]['value']
		if not password:
			password = 'admin'

		ipmi = 'ipmitool -I lanplus -H %s -U %s -P %s chassis power %s' \
			% (ipmi_ip, username, password, cmd)

		cmd_output = _exec(shlex.split(ipmi))
		out = cmd_output.stdout
		err = cmd_output.stderr
		if err:
			raise CommandError(self, err)
		return out
