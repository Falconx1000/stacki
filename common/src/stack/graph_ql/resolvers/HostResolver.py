# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import graphene
from promise import Promise
from promise.dataloader import DataLoader
from stack.db import db
from collections import namedtuple
from stack.graph_ql.inputs import HostInput

class Host(graphene.ObjectType):
	id = graphene.Int()
	name = graphene.String()
	rack = graphene.String()
	rank = graphene.String()
	appliance = graphene.String()
	os = graphene.String()
	box = graphene.String()
	environment = graphene.String()
	osaction = graphene.String()
	installaction = graphene.String()
	comment = graphene.String()
	metadata = graphene.String()
	# interfaces = graphene.List(lambda: Interface)

class Query:
	all_hosts = graphene.List(Host)
 
	def resolve_all_hosts(self, info, **kwargs):
		db.execute(
			"""
			select n.id as id, n.name as name, n.rack as rack, n.rank as rank,
			n.comment as comment, n.metadata as metadata,	a.name as appliance,
			o.name as os, b.name as box, e.name as environment,
			bno.name as osaction, bni.name as installaction
			from nodes n
			left join appliances a   on n.appliance     = a.id
			left join boxes b        on n.box           = b.id
			left join environments e on n.environment   = e.id
			left join bootnames bno  on n.osaction      = bno.id
			left join bootnames bni  on n.installaction = bni.id
			left join oses o	 on b.os            = o.id
			"""
		)

		return [Host(**host) for host in db.fetchall()]

class AddHost(graphene.Mutation):
	class Arguments:
		input = HostInput()
	
	ok = graphene.Boolean()

	def mutate(root, info, input):
		db.execute("""
			insert into nodes
			(name, appliance, box, rack, rank)
			values (
				%s, %s, %s,
			 	(select id from appliances where name=%s),
			 	(select id from boxes      where name=%s)
			) 
			""", (
				input['name'],
				input['rack'],
				input['rank'],
				input['appliance'],
				input['box'],
				)
			)
		print(db.fetchall())
		ok = True
		return AddHost(ok=ok)

class Mutations(graphene.ObjectType):
	add_host = AddHost.Field()