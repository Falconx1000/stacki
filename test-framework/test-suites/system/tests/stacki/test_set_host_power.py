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
		power_count = 0
		for line in result.stdout.splitlines():
			if "Chassis Power is on" in line:
				power_count += 1
		assert power_count == 2

	def test_invalid_command(self, host):
		result = host.run('stack set host power backend-0-0 command="invalid_command"')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - "command" parameter must be "on", "off", "reset"
			{host ...} {command=string} [debug=boolean] [use-method=string]
		''')

	def test_invalid_host(self, host):
		result = host.run('stack set host power invalid_host command="status"')
		assert result.rc == 255
		assert result.stderr.strip() == 'error - cannot resolve host "invalid_host"'

	def test_invalid_ipmi(self, host):
		result = host.run('stack set host power backend-0-0 command="status" debug=y use-method=ipmi')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - Could not set power cmd status on host backend-0-0:
			Attempting to set power via ipmi
			error - backend-0-0 missing ipmi interface.
	''')
