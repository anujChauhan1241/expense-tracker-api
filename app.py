from flask import Flask
from flask_jwt_extended import JWTManager

from flask_migrate import Migrate
from config import Config
from models import db

from routes import (
    get_expenses,
    add_expense,
    update_expense,
    delete_expense,
    patch_expense,
    expense_summary,
    register,
    login
)


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

migrate = Migrate(app, db)

jwt = JWTManager(app)


# ---------- Routes ----------

app.add_url_rule(
    "/expenses",
    view_func=get_expenses,
    methods=["GET"]
)

app.add_url_rule(
    "/expenses",
    view_func=add_expense,
    methods=["POST"]
)

app.add_url_rule(
    "/expenses/summary",
    view_func=expense_summary,
    methods=["GET"]
)

app.add_url_rule(
    "/expenses/<int:id>",
    view_func=update_expense,
    methods=["PUT"]
)

app.add_url_rule(
    "/expenses/<int:id>",
    view_func=delete_expense,
    methods=["DELETE"]
)

app.add_url_rule(
    "/expenses/<int:id>",
    view_func=patch_expense,
    methods=["PATCH"]
)

app.add_url_rule(
    "/auth/register",
    view_func=register,
    methods=["POST"]
)

app.add_url_rule(
    "/auth/login",
    view_func=login,
    methods=["POST"]
)


# ---------- Run ----------

if __name__ == "__main__":
    app.run(debug=True)