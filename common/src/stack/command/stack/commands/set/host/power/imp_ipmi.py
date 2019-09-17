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
		username = ''
		password = ''

		# See if the host has an ipmi interface, raise an error if not
		for interface in self.owner.call('list.host.interface', args = [host]):
			if interface['interface'] == 'ipmi':
				ipmi_ip = interface['ip']
				break
		if not ipmi_ip:
			raise CommandError(self, f'{host} missing ipmi interface.')

		# Try to get ipmi username/passwords, otherwise try defaults
		try:
			username = self.owner.call('list.host.attr', args = [host, 'attr=ipmi_username'])[0].get('value')
		except IndexError:
			pass
		if not username:
			username = 'root'

		try:
			password = self.owner.call('list.host.attr', args = [host, 'attr=ipmi_password'])[0].get('value')
		except IndexError:
			pass
		if not password:
			password = 'admin'

		ipmi = f'ipmitool -I lanplus -H {ipmi_ip} -U {username} -P {password} chassis power {cmd}'

		cmd_output = _exec(ipmi, shlexsplit=True)
		out = cmd_output.stdout
		err = cmd_output.stderr
		if cmd_output.returncode != 0:
			raise CommandError(self, err)
		return out
