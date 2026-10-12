
import os

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    redirect, url_for, session
)
from pymysql.err import IntegrityError

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("SESSION_SECRET is missing from .env")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("todos"))
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():
    errors = []
    values = {"name": "", "email": ""}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password", ""
        )

        values = {"name": name, "email": email}

        # Server-side validation
        if not name:
            errors.append("Name is required")

        if not email:
            errors.append("Email is required")

        if not password:
            errors.append("Password is required")

        if not confirm_password:
            errors.append("Confirm password is required")

        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match")

        if len(name) > 100:
            errors.append("Name must be at most 100 characters")

        if len(email) > 255:
            errors.append("Email must be at most 255 characters")

        # bcrypt only uses up to 72 password bytes
        if len(password.encode("utf-8")) > 72:
            errors.append("Password must be at most 72 bytes")

        if not errors:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            connection = None
            try:
                connection = get_db_connection()

                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users (email, name, password_hash)
                        VALUES (%s, %s, %s)
                        """,
                        (email, name, password_hash),
                    )
                    new_user_id = cursor.lastrowid

                connection.commit()

                # Log the new user in after registration
                session.clear()
                session["user_id"] = new_user_id
                session["name"] = name

                return redirect(url_for("todos"))

            except IntegrityError as exc:
                if exc.args and exc.args[0] == 1062:
                    errors.append("Email Already Exists")
                else:
                    app.logger.exception("Database integrity error")
                    errors.append("Could not complete registration.")

            except pymysql.MySQLError:
                app.logger.exception("Database operation failed")
                errors.append("Database error. Please try again.")

            finally:
                if connection is not None:
                    connection.close()

    return render_template(
        "register.html",
        errors=errors,
        values=values,
    )


# The real private task


# The real private task
@app.route("/todos")
def todos():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    error = request.args.get("error")
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT todo_id, title, is_done, created_at
                FROM todos
                WHERE user_id = %s
                ORDER BY created_at DESC, todo_id DESC
                """,
                (session["user_id"],),
            )
            todos_list = cursor.fetchall()

    except pymysql.MySQLError:
        app.logger.exception("Could not load tasks")
        return "Could not load your tasks. Please try again.", 500

    finally:
        if connection is not None:
            connection.close()

    return render_template(
        "todos.html",
        todos=todos_list,
        name=session.get("name", ""),
        error=error,
    )


# the login part; 
@app.route("/login", methods=["GET", "POST"])
def login():
    errors = []
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email:
            errors.append("Email is required")

        if not password:
            errors.append("Password is required")

        if not errors:
            connection = None

            try:
                connection = get_db_connection()

                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT user_id, name, email, password_hash
                        FROM users
                        WHERE email = %s
                        """,
                        (email,),
                    )
                    user = cursor.fetchone()

                if (
                    user is not None
                    and bcrypt.checkpw(
                        password.encode("utf-8"),
                        user["password_hash"].encode("utf-8"),
                    )
                ):
                    session.clear()
                    session["user_id"] = user["user_id"]
                    session["name"] = user["name"]

                    return redirect(url_for("todos"))

                errors.append("Invalid email or password")

            except pymysql.MySQLError:
                app.logger.exception("Database operation failed")
                errors.append("Database error. Please try again.")

            except ValueError:
                # For example, if a stored password hash is invalid.
                app.logger.exception("Invalid stored password hash")
                errors.append("Could not log in. Please try again.")

            finally:
                if connection is not None:
                    connection.close()

    return render_template(
        "login.html",
        errors=errors,
        email=email,
    )

@app.route("/todos/add", methods=["POST"])
def add_todo():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()

    if not title:
        return redirect(url_for("todos", error="Title is required"))

    if len(title) > 200:
        return redirect(url_for("todos", error="Title is too long"))

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO todos (user_id, title)
                VALUES (%s, %s)
                """,
                (session["user_id"], title),
            )

        connection.commit()

    except pymysql.MySQLError:
        app.logger.exception("Could not add task")
        return "Could not add your task. Please try again.", 500

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
def toggle_todo(todo_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE todos
                SET is_done = CASE WHEN is_done = 1 THEN 0 ELSE 1 END
                WHERE todo_id = %s AND user_id = %s
                """,
                (todo_id, session["user_id"]),
            )

        connection.commit()

    except pymysql.MySQLError:
        app.logger.exception("Could not update task")
        return "Could not update your task. Please try again.", 500

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for("todos"))

@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM todos
                WHERE todo_id = %s AND user_id = %s
                """,
                (todo_id, session["user_id"]),
            )

        connection.commit()

    except pymysql.MySQLError:
        app.logger.exception("Could not delete task")
        return "Could not delete your task. Please try again.", 500

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for("todos"))

@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
def edit_todo(todo_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()

    if not title:
        return redirect(url_for("todos", error="Title is required"))

    if len(title) > 200:
        return redirect(url_for("todos", error="Title is too long"))

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE todos
                SET title = %s
                WHERE todo_id = %s AND user_id = %s
                """,
                (title, todo_id, session["user_id"]),
            )

        connection.commit()

    except pymysql.MySQLError:
        app.logger.exception("Could not edit task")
        return "Could not edit your task. Please try again.", 500

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for("todos"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
    

