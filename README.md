# Expense Tracker API

A RESTful Expense Tracker API built using **Python, Flask, SQLAlchemy, and SQLite**. The project supports user authentication, secure expense management, filtering, pagination, sorting, and monthly expense summaries.

## Features

- **User Authentication:** Registration and login with hashed passwords.
- **JWT Authorization:** Protected API endpoints using JSON Web Tokens.
- **Expense CRUD:** Create, read, update, partially update, and delete expenses.
- **User Data Isolation:** Users can access and manage only their own expenses.
- **Filtering:** Filter expenses by title, category, amount range, and date range.
- **Pagination:** Retrieve expenses in manageable pages.
- **Sorting:** Sort expenses by supported fields and direction.
- **Monthly Summary:** Retrieve expense summaries for a specified month and year.
- **Input Validation:** Validate incoming data and return appropriate HTTP status codes.
- **Database Migrations:** Manage schema changes using Flask-Migrate and Alembic.

## Tech Stack

- Python 3.11
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Migrate and Alembic
- Flask-JWT-Extended
- Werkzeug
- uv
- Postman

## Project Structure

expenseTracker API/
├── app.py
├── config.py
├── models.py
├── routes.py
├── migrations/
├── src/
├── .env
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md


## Getting Started

### 1. Clone the repository

git clone <YOUR_REPOSITORY_URL>
cd expense-tracker-api


Replace `<YOUR_REPOSITORY_URL>` with your GitHub repository URL.

### 2. Install dependencies

Install Python 3.11 and [uv](https://docs.astral.sh/uv/) if they are not already installed.


uv sync


### 3. Configure environment variables

Create a `.env` file in the project root:

JWT_SECRET_KEY=replace_with_a_secure_random_secret


Use a strong, randomly generated secret. Never commit your `.env` file or expose your JWT secret.

### 4. Initialize the database

Run the existing migrations:

uv run flask --app app db upgrade


### 5. Start the development server

uv run python app.py


The API should be available at:

http://127.0.0.1:5000

## API Endpoints

All expense endpoints require a valid JWT access token.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Log in and obtain an access token |
| GET | `/expenses` | Retrieve expenses |
| POST | `/expenses` | Create an expense |
| GET | `/expenses/summary` | Retrieve a monthly summary |
| PUT | `/expenses/<id>` | Update an expense |
| PATCH | `/expenses/<id>` | Partially update an expense |
| DELETE | `/expenses/<id>` | Delete an expense |

### Authentication

After logging in, copy the returned access token into Postman.

Under **Authorization**, select **Bearer Token** and paste the token.

Alternatively, send this HTTP header:


Authorization: Bearer <YOUR_ACCESS_TOKEN>


### Expense Example

Example request body for creating an expense:

{
  "title": "Lunch",
  "amount": 150,
  "category": "Food"
}


### Filtering and Pagination

The GET `/expenses` endpoint supports filtering, pagination, and sorting.

Example:

GET /expenses?page=1&limit=10&category=Food&min_amount=50&max_amount=500


Additional supported filters include title and date range. Sorting is available through the endpoint's supported sort parameters.

### Monthly Summary

Example:

GET /expenses/summary?month=10&year=2026


Use the month and year you want to analyze.

## Database Migrations

This project uses Flask-Migrate and Alembic to manage database schema changes.

Generate a migration after modifying models:

uv run flask --app app db migrate -m "Describe schema change"


Apply migrations:

uv run flask --app app db upgrade


## Testing

The API was tested using Postman, including:

- User registration and login
- JWT-protected endpoints
- Expense CRUD operations
- Filtering and pagination
- Monthly summaries
- Cross-user access restrictions

## Future Improvements

- Automated unit and integration tests
- API documentation with Swagger/OpenAPI
- Deployment to a cloud platform
- Budget limits and spending analytics

## Author

Developed as a backend learning project to practice REST API development, authentication, relational databases, database migrations, and API security.
