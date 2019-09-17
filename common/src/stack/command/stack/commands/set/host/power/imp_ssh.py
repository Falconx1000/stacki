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

		# Unlike ipmi, ssh has no way to start a host that is off
		# We still have to handle the command however
		if cmd == 'on':
			raise CommandError(self, f'Cannot use ssh to start host {host}')

		elif cmd == 'off':
			cmd_output = _exec(f'ssh {host} "shutdown -h now"', shlexsplit=True)
			out = cmd_output.stdout
			err = cmd_output.stderr
			if cmd_output.returncode != 0:
				raise CommandError(self, err)

		elif cmd == 'reset':
			cmd_output = _exec(f'ssh {host} "reboot"', shlexsplit=True)
			out = cmd_output.stdout
			err = cmd_output.stderr

			# After issueing a reboot, ssh will send a Connection closed message in stderr
			# We shouldn't raise an error because of this
			if cmd_output.returncode != 0 and f'Connection to {host} closed by remote host' not in err:
				raise CommandError(self, err)

		elif cmd == 'status':

			# If we can run a command on the remote host, it's up
			cmd_output = _exec(f'ssh {host} "hostname"', shlexsplit=True)
			out = cmd_output.stdout
			err = cmd_output.stderr
			if cmd_output.returncode != 0:
				raise CommandError(self, f'Chassis Power is unreachable via ssh:\n{err}')
			else:
				return f'Chassis Power is on'
