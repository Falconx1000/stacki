from datetime import timedelta
from pathlib import Path

from ariadne import QueryType, graphql_sync, gql, make_executable_schema
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import (
	JWTManager, get_jwt_identity, jwt_optional,
	jwt_required, set_access_cookies
)
import requests


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Path("/opt/stack/etc/jwt.secret").read_text()
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_ERROR_MESSAGE_KEY"] = "error"
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/graphql/playground"
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
def redirect_to_playground():
	return redirect(url_for("playground"))


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


@app.route("/playground", methods=["GET"])
@jwt_optional
def playground():
	current_user = get_jwt_identity()
	token = request.cookies.get("access_token_cookie")
	if current_user and token:
		return render_template("index.html", token=token)

	return redirect(url_for("login"))


@app.route("/playground/login", methods=["GET", "POST"])
def login():
	error = None
	if request.method == 'POST':
		# Try to get a JWT token
		data = {
			"username": request.form.get("username", ""),
			"password": request.form.get("password", "")
		}

		token_data = requests.post("http://localhost/api/token", data=data).json()
		if "token" in token_data:
			# We're going to redirect to the playground
			response = redirect(url_for("playground"))

			# Send back the JWT token as a cookie
			set_access_cookies(response, token_data["token"])

			return response
		elif "error" in token_data:
			error = response["error"]
		else:
			error = "Unknown failure to authenticate"

	return render_template("login.html", error=error)
