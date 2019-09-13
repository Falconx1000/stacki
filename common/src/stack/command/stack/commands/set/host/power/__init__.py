# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.mq
import socket
import json
import re
from glob import glob
from pathlib import Path
from stack.exception import ArgRequired, ParamError, CommandError

class Command(stack.commands.set.host.command):
	"""
	Sends a "power" command to a host. Valid power commands are: on, off and reset. This
	command uses IPMI for hardware based hosts to change the power setting.

	<arg type='string' name='host' repeat='1'>
	One or more host names.
	</arg>

	<param type='string' name='command' optional='0'>
	The power command to execute. Valid power commands are: "on", "off" and "reset".
	</param>

	<param type='boolean' name='debug' optional='1'>
	Print debug output from the command. For ipmi capable hosts, prints
	the output from ipmitool.
	</param>

	<param type='string' name='force' optional='1'>
	Force a method for setting power on a host.
	</param>

	<example cmd='set host power stacki-1-1 command=reset'>
	Performs a hard power reset on host stacki-1-1.
	</example>

	<example cmd='set host power stacki-1-1 command=off force=ssh'>
	Turns off host stacki-1-1 using ssh.
	</example>
	"""
	def mq_publish(self, host, cmd):
		ttl = 60*10
		if cmd == 'off':
			ttl = -1

		msg = { 'source' : host,
			'channel': 'health',
			'ttl'    : ttl,
			'payload': '{"state": "power %s"}' % cmd }

		tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		tx.sendto(json.dumps(msg).encode(),
			  ('127.0.0.1', stack.mq.ports.publish))
		tx.close()

	def run(self, params, args):
		if not len(args):
			raise ArgRequired(self, 'host')

		cmd, debug, force_imp = self.fillParams([
			('command', None, True),
			('debug', False),
			('force', None)
		])
		power_imp = []
		if cmd not in [ 'on', 'off', 'reset', 'status' ]:
			raise ParamError(self, 'command', 'must be "on", "off", "reset", or "status"')

		# Get all the set power implemenations
		# Besides ipmi and ssh
		power_imp = [imp for imp in glob(f'{Path(__file__).parent}/imp_*.py') if 'ssh' not in imp and 'ipmi' not in imp]
		imp_names = re.findall('imp_(.*).py', '\n'.join(power_imp))
		self.debug = self.str2bool(debug)

		for host in self.getHostnames(args):
			debug_msgs = []
			msgs = []
			self.beginOutput()

			imp = 'ipmi'
			if force_imp:
				imp = force_imp

			# Try using ipmi first
			# Unless the force param is set
			try:
				debug_msgs.append(f'Attempting to set power via {imp}')
				ipmi_msg = self.runImplementation(imp, [host, cmd])
				self.mq_publish(host, cmd)
				msgs.append(ipmi_msg)
			except CommandError as msg:
				debug_msgs.append(f'{imp} failed to set power cmd {cmd}: {msg}')
				# If the force flag was set
				# only run that implementation
				if imp == force_imp:
					debug_str = '\n'.join(debug_msgs)
					self.endOutput(padChar='', trimOwner=True)
					raise CommandError(self, f'Could not set power cmd {cmd} on host {host}\n{debug_str}')
				for imp in imp_names:
					debug_msgs.append(f'Attempting to set power via {imp}')
					try:
						imp_msg = self.runImplementation(imp, [host, cmd])
						msgs.append(str(imp_msg))
						self.mq_publish(host, cmd)
						break
					except CommandError as imp_error:
						debug_msgs.append(str(imp_error))
				if not msgs:
					try:
						debug_msgs.append('Attempting to set power via ssh')
						ssh_msg = self.runImplementation('ssh', [host, cmd])
						msgs.append(str(ssh_msg))
						self.mq_publish(host, cmd)
					except CommandError as ssh_error:
						debug_msgs.append(str(ssh_error))
						if debug_msgs:
							debug_str = '\n'.join(debug_msgs)
							raise CommandError(self, f'Could not set power cmd {cmd} on host {host}\n{debug_str}')
						else:
							raise CommandError(self, f'Could not set power cmd {cmd} on host {host}')
			if self.debug:
				self.addOutput(host, '\n'.join(msgs))
				self.addOutput(host, '\n'.join(debug_msgs))
				self.endOutput(padChar='', trimOwner=True)
			else:
				self.addOutput(host, '\n'.join(msgs))
				self.endOutput(padChar='', trimOwner=True)
