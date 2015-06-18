# @SI_Copyright@
# @SI_Copyright@

import stack.commands.set.network

class Command(stack.commands.set.network.command):
	"""
	Sets the DNS zone (domain name) for a network.

        <arg type='string' name='network' optional='0' repeat='0'>
        The name of the network.
	</arg>
	
	<param type='string' name='zone' optional='0'>
        Zone that the named network should have.
	</param>
	
	<example cmd='set network zone ipmi zone=ipmi'>
        Sets the "ipmi" network zone to "ipmi".
	</example>
	"""
                
        def run(self, params, args):

                (networks, zone) = self.fillSetNetworkParams(args, 'zone')
                if len(networks) > 1:
                        self.abort('must specify a single network')
			        	
        	for network in networks:
			self.db.execute("""
                        	update subnets set zone='%s' where
				subnets.name='%s'
                                """ % (zone, network))

