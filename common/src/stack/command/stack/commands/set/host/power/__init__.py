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

	<param type='string' name='use-method' optional='1'>
	Set a desired method for communicating to hosts, possible methods
	include but are not limited to ipmi and ssh.
	</param>

	<example cmd='set host power stacki-1-1 command=reset'>
	Performs a hard power reset on host stacki-1-1.
	</example>

	<example cmd='set host power stacki-1-1 command=off use-method=ssh'>
	Turns off host stacki-1-1 using ssh.
	</example>
	"""
	def mq_publish(self, host, cmd):
		"""
		Publish the power status to the
		message queue
		"""

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
			('use-method', None)
		])
		power_imp = []
		self.debug = self.str2bool(debug)

		# The first implementation is ipmi by defualt
		# but can be forced by the use-method parameter
		# If this is set, only that implementation will be run
		imp = 'ipmi'
		imp_success = False
		if force_imp:
			imp = force_imp

		# Gather all set power implmentations besides ipmi and ssh
		power_imp = [imp for imp in glob(f'{Path(__file__).parent}/imp_*.py') if 'ssh' not in imp and 'ipmi' not in imp]

		# Extract the unique implementation names
		other_imp = re.findall('imp_(.*).py', '\n'.join(power_imp))

		imp_names = [imp]

		# Add any additional implementations to the list
		for method in other_imp:
			imp_names.append(method)

		# End with ssh
		imp_names.append('ssh')

		if cmd not in [ 'on', 'off', 'reset', 'status' ]:
			raise ParamError(self, 'command', 'must be "on", "off", "reset"')

		for host in self.getHostnames(args):
			debug_msgs = []

			# msgs gathers the normal output of the command
			msgs = []
			self.beginOutput()

			for imp in imp_names:
				debug_msgs.append(f'Attempting to set power via {imp}')
				try:
					imp_msg = self.runImplementation(imp, [host, cmd])
					if imp_msg:
						msgs.append(str(imp_msg))
					self.mq_publish(host, cmd)

					# Set the flag since a CommandError
					# wasn't raised when running the implementation
					# so it succeeded
					imp_success = True
					break
				except CommandError as imp_error:
					debug_msgs.append(str(imp_error))

					# if force_imp was set, don't try any
					# other implementations
					if force_imp:
						break

			msg_output = []
			if msgs:
				msg_output = '\n'.join(msgs)

			# debug_msgs will have always at least one entry
			debug_output = '\n'.join(debug_msgs)
			if self.debug:
				self.addOutput(host, msg_output)
				self.addOutput(host, debug_output)
			elif msgs:
				self.addOutput(host, msg_output)
			self.endOutput(padChar='', trimOwner=True)

			# Raise a CommandError if no implementation worked
			if not imp_success:
				if self.debug:
					raise CommandError(self, f'Could not set power cmd {cmd} on host {host}:\n{debug_output}')
				else:
					raise CommandError(self, f'Could not set power cmd {cmd} on host {host}')
