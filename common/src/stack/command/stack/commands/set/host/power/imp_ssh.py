# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import shlex
from stack.util import _exec
from stack.exception import CommandError

class Implementation(stack.commands.Implementation):
	def run(self, args):
		host = args[0]
		cmd = args[1]

		if cmd == 'on':
			raise CommandError(self, f'Cannot use ssh to start host {host}')

		if cmd == 'off':
			cmd_output = _exec(shlex.split(f'ssh {host} "shutdown -h now"'))
			out = cmd_output.stdout
			err = cmd_output.stderr
			if cmd_output.returncode != 0:
				raise CommandError(self, err)

		if cmd == 'reset':
			cmd_output = _exec(shlex.split(f'ssh {host} "reboot"'))
			out = cmd_output.stdout
			err = cmd_output.stderr
			if cmd_output.returncode != 0:
				raise CommandError(self, err)

		if cmd == 'status':
			cmd_output = _exec(shlex.split(f'ssh {host} "hostname"'))
			out = cmd_output.stdout
			err = cmd_output.stderr
			if cmd_output.returncode != 0:
				raise CommandError(self, f'Chassis Power is unreachable via ssh:\n{err}')
			else:
				return f'Chassis Power is on'
