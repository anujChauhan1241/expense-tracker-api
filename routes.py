from datetime import datetime, timedelta

from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required
)
from sqlalchemy import func, or_
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from models import db, Expense, User


# ---------------- RESPONSE HELPERS ----------------

def success_response(data, status=200):
    return jsonify({
        "success": True,
        "data": data
    }), status


def error_response(message, status=400):
    return jsonify({
        "success": False,
        "error": message
    }), status


def get_current_user_id():
    # Login stores the user ID as a string in the JWT.
    return int(get_jwt_identity())


def parse_date(value, field_name):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError(
            f"{field_name} must use YYYY-MM-DD format"
        )


# ---------------- AUTH: REGISTER ----------------

def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response("A valid JSON body is required")

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all(
        isinstance(value, str)
        for value in (username, email, password)
    ):
        return error_response(
            "username, email and password must be strings"
        )

    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return error_response(
            "username, email and password are required"
        )

    if len(username) > 80:
        return error_response("username cannot exceed 80 characters")

    if len(email) > 120:
        return error_response("email cannot exceed 120 characters")

    if len(password) < 6:
        return error_response(
            "password must contain at least 6 characters"
        )

    existing_user = User.query.filter(
        or_(
            User.username == username,
            User.email == email
        )
    ).first()

    if existing_user:
        return error_response(
            "Username or email already registered",
            409
        )

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
    )

    try:
        db.session.add(user)
        db.session.commit()

        return success_response({
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }, 201)

    except Exception:
        db.session.rollback()
        return error_response(
            "Could not register user",
            500
        )


# ---------------- AUTH: LOGIN ----------------

def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response("A valid JSON body is required")

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return error_response("email and password are required")

    email = email.strip().lower()

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(
        user.password, password
    ):
        return error_response("Invalid email or password", 401)

    access_token = create_access_token(
        identity=str(user.id)
    )

    return success_response({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })


# ---------------- EXPENSE VALIDATION ----------------

def validate_expense(data, partial=False):
    if not isinstance(data, dict):
        return None, "A valid JSON object is required"

    allowed_fields = {"title", "amount", "category"}

    if not partial and not {"title", "amount"}.issubset(data):
        return None, "title and amount are required"

    if not partial and not set(data).issubset(allowed_fields):
        return None, "Unsupported expense field"

    if partial and not data:
        return None, "Provide at least one field to update"

    if partial and not set(data).issubset(allowed_fields):
        return None, "Unsupported expense field"

    cleaned = {}

    if "title" in data:
        title = data["title"]

        if not isinstance(title, str):
            return None, "title must be a string"

        title = title.strip()

        if not title:
            return None, "title cannot be empty"

        if len(title) > 100:
            return None, "title cannot exceed 100 characters"

        cleaned["title"] = title

    if "amount" in data:
        amount = data["amount"]

        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(amount, bool) or not isinstance(
            amount, (int, float)
        ):
            return None, "amount must be a number"

        if amount <= 0:
            return None, "amount must be greater than zero"

        cleaned["amount"] = float(amount)

    if "category" in data:
        category = data["category"]

        if category is not None and not isinstance(category, str):
            return None, "category must be a string or null"

        if isinstance(category, str):
            category = category.strip()

            if not category:
                return None, "category cannot be empty"

            if len(category) > 50:
                return None, "category cannot exceed 50 characters"

        cleaned["category"] = category

    return cleaned, None


def expense_to_dict(expense):
    return {
        "id": expense.id,
        "title": expense.title,
        "amount": expense.amount,
        "category": expense.category,
        "created_at": (
            expense.created_at.isoformat()
            if expense.created_at else None
        ),
        "user_id": expense.user_id
    }


# ---------------- GET EXPENSES ----------------

@jwt_required()
def get_expenses():
    user_id = get_current_user_id()

    # Critical: users can only query their own expenses.
    query = Expense.query.filter_by(user_id=user_id)

    args = request.args

    # Amount filters
    try:
        if "min_amount" in args:
            min_amount = float(args["min_amount"])

            if min_amount < 0:
                return error_response("min_amount cannot be negative")

            query = query.filter(Expense.amount >= min_amount)

        if "max_amount" in args:
            max_amount = float(args["max_amount"])

            if max_amount < 0:
                return error_response("max_amount cannot be negative")

            query = query.filter(Expense.amount <= max_amount)

    except ValueError:
        return error_response(
            "min_amount and max_amount must be numbers"
        )

    if (
        "min_amount" in args
        and "max_amount" in args
        and float(args["min_amount"]) > float(args["max_amount"])
    ):
        return error_response(
            "min_amount cannot exceed max_amount"
        )

    # Text filters
    title = args.get("title")
    if title:
        query = query.filter(
            Expense.title.ilike(f"%{title.strip()}%")
        )

    category = args.get("category")
    if category:
        query = query.filter(
            Expense.category.ilike(f"%{category.strip()}%")
        )

    # Date filters: inclusive calendar dates
    try:
        if args.get("start_date"):
            start_date = parse_date(
                args["start_date"], "start_date"
            )
            query = query.filter(
                Expense.created_at >= start_date
            )

        if args.get("end_date"):
            end_date = parse_date(
                args["end_date"], "end_date"
            )
            query = query.filter(
                Expense.created_at < end_date + timedelta(days=1)
            )

        if args.get("start_date") and args.get("end_date"):
            if start_date > end_date:
                return error_response(
                    "start_date cannot be after end_date"
                )

    except ValueError as exc:
        return error_response(str(exc))

    # Sorting uses an allowlist; never pass arbitrary user input to SQL.
    sort_options = {
        "amount": Expense.amount.asc(),
        "-amount": Expense.amount.desc(),
        "title": Expense.title.asc(),
        "-title": Expense.title.desc(),
        "created_at": Expense.created_at.asc(),
        "-created_at": Expense.created_at.desc()
    }

    sort_by = args.get("sort", "-created_at")

    if sort_by not in sort_options:
        return error_response(
            "Invalid sort. Use amount, -amount, title, "
            "-title, created_at or -created_at"
        )

    query = query.order_by(sort_options[sort_by])

    # Pagination
    try:
        page = int(args.get("page", 1))
        limit = int(args.get("limit", 10))
    except ValueError:
        return error_response("page and limit must be integers")

    if page < 1:
        return error_response("page must be at least 1")

    if limit < 1 or limit > 100:
        return error_response("limit must be between 1 and 100")

    total = query.count()
    expenses = query.offset((page - 1) * limit).limit(limit).all()

    return success_response({
        "expenses": [expense_to_dict(e) for e in expenses],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    })


# ---------------- CREATE EXPENSE ----------------

@jwt_required()
def add_expense():
    data = request.get_json(silent=True)
    cleaned, error = validate_expense(data)

    if error:
        return error_response(error)

    expense = Expense(
        title=cleaned["title"],
        amount=cleaned["amount"],
        category=cleaned.get("category"),
        user_id=get_current_user_id(),
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(expense)
        db.session.commit()

        return success_response(
            expense_to_dict(expense), 201
        )

    except Exception:
        db.session.rollback()
        return error_response("Could not create expense", 500)


# ---------------- UPDATE EXPENSE: PUT ----------------

@jwt_required()
def update_expense(id):
    user_id = get_current_user_id()

    expense = Expense.query.filter_by(
        id=id,
        user_id=user_id
    ).first()

    if not expense:
        return error_response("Expense not found", 404)

    data = request.get_json(silent=True)
    cleaned, error = validate_expense(data)

    if error:
        return error_response(error)

    expense.title = cleaned["title"]
    expense.amount = cleaned["amount"]
    expense.category = cleaned.get("category")

    try:
        db.session.commit()
        return success_response(expense_to_dict(expense))

    except Exception:
        db.session.rollback()
        return error_response("Could not update expense", 500)


# ---------------- PARTIAL UPDATE: PATCH ----------------

@jwt_required()
def patch_expense(id):
    user_id = get_current_user_id()

    expense = Expense.query.filter_by(
        id=id,
        user_id=user_id
    ).first()

    if not expense:
        return error_response("Expense not found", 404)

    data = request.get_json(silent=True)
    cleaned, error = validate_expense(data, partial=True)

    if error:
        return error_response(error)

    for field, value in cleaned.items():
        setattr(expense, field, value)

    try:
        db.session.commit()
        return success_response(expense_to_dict(expense))

    except Exception:
        db.session.rollback()
        return error_response("Could not patch expense", 500)


# ---------------- DELETE EXPENSE ----------------

@jwt_required()
def delete_expense(id):
    user_id = get_current_user_id()

    expense = Expense.query.filter_by(
        id=id,
        user_id=user_id
    ).first()

    if not expense:
        return error_response("Expense not found", 404)

    try:
        db.session.delete(expense)
        db.session.commit()

        return success_response({
            "message": "Expense deleted successfully",
            "id": id
        })

    except Exception:
        db.session.rollback()
        return error_response("Could not delete expense", 500)


# ---------------- MONTHLY SUMMARY ----------------

@jwt_required()
def expense_summary():
    user_id = get_current_user_id()
    now = datetime.now()

    try:
        month = int(request.args.get("month", now.month))
        year = int(request.args.get("year", now.year))
    except ValueError:
        return error_response("month and year must be integers")

    if month < 1 or month > 12:
        return error_response("month must be between 1 and 12")

    if year < 1 or year > 9998:
        return error_response("year is invalid")

    start_date = datetime(year, month, 1)

    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    base_query = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at < next_month
    )

    total_expense = (
        base_query.with_entities(
            func.coalesce(func.sum(Expense.amount), 0.0)
        ).scalar()
    )

    expense_count = base_query.count()

    category_rows = (
        base_query.with_entities(
            Expense.category,
            func.sum(Expense.amount)
        )
        .group_by(Expense.category)
        .all()
    )

    category_totals = {
        category or "Uncategorized": float(total or 0)
        for category, total in category_rows
    }

    return success_response({
        "month": month,
        "year": year,
        "total_expense": float(total_expense or 0),
        "expense_count": expense_count,
        "category_totals": category_totals
    })
