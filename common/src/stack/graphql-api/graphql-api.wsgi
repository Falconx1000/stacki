from ariadne import QueryType, graphql_sync, gql, make_executable_schema
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify


type_defs = gql("""
    type Query {
	hello: String!
    }
""")

query = QueryType()

@query.field("hello")
def resolve_hello(*_):
    return "Hello!"

schema = make_executable_schema(type_defs, query)
application = Flask(__name__)

@application.route("/", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200

@application.route("/", methods=["POST"])
def graphql_server():
    success, result = graphql_sync(
        schema,
        request.get_json(),
        context_value=request,
        debug=application.debug
    )

    return jsonify(result), 200 if success else 400
