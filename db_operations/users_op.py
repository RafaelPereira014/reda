from datetime import datetime
from config import DB_CONFIG  # Import the database configuration
from flask import session
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def get_details(userid):
    """Get the user ID for the given username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE id=%s", (userid,))
    user = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    return user

def is_admin(user_id):
    """Checks if the user is an Admin"""
    conn = connect_to_database()
    cursor = conn.cursor()

    # Fetch role_id from Users table
    cursor.execute("SELECT role_id FROM Users WHERE id = %s", (user_id,))
    user_type = cursor.fetchone()

    if user_type:
        role_id = user_type[0]

        # Query Roles table to check if role_id corresponds to 'admin'
        cursor.execute("SELECT type FROM Roles WHERE id = %s AND type = 'admin'", (role_id,))
        admin_role = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin_role:
            return True
        else:
            return False
    else:
        cursor.close()
        conn.close()
        return False