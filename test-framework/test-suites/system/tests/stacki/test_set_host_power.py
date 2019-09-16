import json
from textwrap import dedent

class TestSetHostPower:
	def test_single_host(self, host):
		result = host.run('stack set host power backend-0-0 command="status"')
		assert result.rc == 0
		assert result.stdout.strip() == 'Chassis Power is on'

	def test_multiple_hosts(self, host):
		result = host.run('stack set host power backend-0-0 backend-0-1 command="status"')
		assert result.rc == 0
		assert result.stdout.strip() == dedent('''\
			Chassis Power is on

			Chassis Power is on

		''').strip()

	def test_invalid_command(self, host):
		result = host.run('stack set host power backend-0-0 command="invalid_command"')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - "command" parameter must be "on", "off", "reset", or "status"
			{host ...} {command=string} [debug=boolean] [force=string]
		''')

	def test_invalid_host(self, host):
		result = host.run('stack set host power invalid_host command="status"')
		assert result.rc == 255
		assert result.stderr.strip() == 'error - cannot resolve host "invalid_host"'

	def test_invalid_ipmi(self, host):
		result = host.run('stack set host power backend-0-0 command="status" force=ipmi')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - Could not set power cmd status on host backend-0-0
			Attempting to set power via ipmi
			ipmi failed to set power cmd status: error - backend-0-0 missing ipmi interface.
	''')
