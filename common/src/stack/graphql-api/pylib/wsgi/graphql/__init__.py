from pathlib import Path

from ariadne import QueryType, graphql_sync, gql, make_executable_schema
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, jsonify, render_template, request
from flask_jwt_extended import JWTManager, jwt_required


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Path("/opt/stack/etc/jwt.secret").read_text()
app.config["JWT_ERROR_MESSAGE_KEY"] = "error"
jwt = JWTManager(app)

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


@app.route("/", methods=["GET"])
def graphql_playground():
	return render_template("index.html", token="TODO"), 200


@app.route("/", methods=["POST"])
@jwt_required
def graphql_endpoint():
	success, result = graphql_sync(
		schema,
		request.get_json(),
		context_value=request,
		debug=app.debug
	)

	return jsonify(result), 200 if success else 400
