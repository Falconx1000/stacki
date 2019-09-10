# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.mq
import socket
import json
from glob import glob
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
	Print debug output from the command. For hardware based hosts, prints
	the output from ipmitool.
	</param>

	<example cmd='set host power stacki-1-1 command=reset'>
	Performs a hard power reset on host stacki-1-1.
	</example>
	"""
	def mq_publish(host, cmd):
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

		cmd, debug, force_imp = self.fillParams([ ('command', None, True), ('debug', False), ('imp', None) ])
		power_imp = []

		if cmd == 'status':
			#
			# used by "stack list host power" -- this is an easy way in which to
			# share code between the two commands
			#
			# set 'debug' to True in order to get output from the status command
			#
			debug = True
		elif cmd not in [ 'on', 'off', 'reset' ]:
			raise ParamError(self, 'command', 'must be "on", "off" or "reset"')

		# Get all the set power implemenations
		# Besides ipmi and ssh
		power_imp = glob('imp_*.py')
		self.debug = self.str2bool(debug)

		for host in self.getHostnames(args):
			debug_msg = ''
			self.beginOutput()

			imp = 'ipmi'
			if force_imp:
				imp = force_imp

			# Try using ipmi first
			# Unless the imp flag is set
			try:
				debug_msg = self.runImplementation(imp, [host, cmd])
				mq_publish(host, cmd)
			except CommandError as msg:
				for imp in power_imp:
					try:
						self.runImplementation(imp, [host, cmd])
						mq_publish(host, cmd)
					except CommandError as imp_error:
						debug_msg = f'Used {imp} implementation on {host} with cmd {cmd}, implmentation {imp} failed with:\n{imp_error}'
						self.addOutput(host, debug_msg)
				try:
					self.runImplementation('ssh', [host, cmd])
					mq_publish(host, cmd)
				except CommandError as ssh_error:
					debug_msg = f'Used ssh implementation on {host} with cmd {cmd}, implmentation {imp} failed with:\n{ssh_error}'
					self.addOutput(host, f'Could not set power on host {host}: {ssh_error}')
				if not self.debug:
					self.endOutput(padChar='', trimOwner=True)
			if self.debug:
				self.addOutput(host, debug_msg)
				self.endOutput(padChar='', trimOwner=True)
