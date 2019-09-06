# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.util import _exec
from stack.exception import CommandError

class Implementation(stack.commands.Implementation):
	def run(self, args):
		host = args[0]
		cmd = args[1]
		ipmi_ip = ''

		for interface in self.call('list.host.interface', [ host ]):
			if interface['interface'] == 'ipmi':
				ipmi_ip = interface['ip']
		if not ipmi_ip:
			raise CommandError(self, f'{host} missing ipmi interface.')

		username = self.getHostAttr(host, 'ipmi_username')
		if not username:
			username = 'root'

		password = self.getHostAttr(host, 'ipmi_password')
		if not password:
			password = 'admin'

		ipmi = 'ipmitool -I lanplus -H %s -U %s -P %s chassis power %s' \
			% (ipmi_ip, username, password, cmd)

		cmd_output = _exec(ipmi)
		out = cmd_output.stdout
		err = cmd_output.stderr
		if err:
			raise CommandError(self, err)
		return out
