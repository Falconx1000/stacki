# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.mq
import socket
import json
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

		cmd, debug = self.fillParams([ ('command', None, True), ('debug', False) ])

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

		self.debug = self.str2bool(debug)

		for host in self.getHostnames(args):
			imp = 'ipmi'
			vm_type = self.getHostAttr(host, 'vm.type')
			if vm_type:
				imp = vm_type
			try:
				debug = self.runImplementation(imp, [host])
			except CommandError as msg:
				debug = msg
			if self.debug:
				self.beginOutput()
				self.addOutput(host, debug)
				self.endOutput(padChar='', trimOwner=True)
			mq_publish(host, cmd)
