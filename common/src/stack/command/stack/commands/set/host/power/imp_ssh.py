# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import subprocess
from stack.exception import CommandError

class Implementation(stack.commands.Implementation):
	def run(self, args):
		host = args[0]
		cmd = args[1]
		out_msg = ''

		# Unlike ipmi, ssh has no way to start a host that is off
		# We still have to handle the command however
		if cmd == 'on':
			raise CommandError(self, f'Cannot use ssh to start host {host}')

		elif cmd == 'off':
			cmd_output = self.owner._exec(
				f'ssh {host} "shutdown -h now"',
				shlexsplit=True,
				stderr=subprocess.STDOUT,
				stdout=subprocess.PIPE
			)
			out = cmd_output.stdout
			if cmd_output.returncode != 0 and f'Connection to {host} closed by remote host' not in out:
				raise CommandError(self, out)
			return out_msg

		elif cmd == 'reset':
			cmd_output = self.owner._exec(
				f'ssh {host} "reboot"',
				shlexsplit=True,
				stderr=subprocess.STDOUT,
				stdout=subprocess.PIPE
			)
			out = cmd_output.stdout

			# After issueing a reboot, ssh will send a Connection closed message in stderr
			# We shouldn't raise an error because of this
			if cmd_output.returncode != 0 and f'Connection to {host} closed by remote host' not in out:
				raise CommandError(self, out)
			return out_msg

		elif cmd == 'status':

			# If we can run a command on the remote host, it's up
			cmd_output = self.owner._exec(
				f'ssh {host} "hostname"',
				shlexsplit=True,
				stderr=subprocess.STDOUT,
				stdout=subprocess.PIPE
			)
			out = cmd_output.stdout
			if cmd_output.returncode != 0:
				raise CommandError(self, f'Chassis Power is unreachable via ssh:\n{out}')
			else:
				out_msg = f'Chassis Power is on\n'
			return out_msg
