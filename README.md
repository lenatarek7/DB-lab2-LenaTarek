# Todo List Web Application

## About the Project
This project was made for Introduction to Database Systems Lab 2 using Python, Flask, and MySQL.

It allows users to register, log in, and manage their own tasks.

## Features
- Register, log in, and log out
- Add, edit, and delete tasks
- Mark tasks as completed or undo them, dark mode

- Validate user input
- Keep each user's tasks private
- Store data in a MySQL database
- Hash passwords using bcrypt

## Requirements
- Python 3.11
- MySQL Server
- MySQL Workbench (optional)

## How to Run

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the required packages:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a `.env` file using `.env.example` and add your MySQL settings and a secret key.

4. Open `database/schema.sql` in MySQL Workbench and run it to create the database and tables.

   **Note:** Running the schema again may delete the existing database and its data.

5. Start the application:

   ```powershell
   python app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.

## How to Use
Register an account, log in, and start adding tasks. You can edit, complete, or delete tasks whenever you want. Each user can only manage their own tasks.

## Technologies
Python, Flask, MySQL, PyMySQL, bcrypt, HTML, and CSS.

## Screenshots
Screenshots of the application are saved in the `screenshots/` folder.

## Author
Created for Introduction to Database Systems Lab 2.
