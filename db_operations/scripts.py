from datetime import datetime
from config import DB_CONFIG  # Import the database configuration
from flask import session
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)





def get_script_details():
    """Get all tools from user and their count."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    scripts_user = []
    scripts_count = 0
    
    try:
        # Query to fetch all tools
        cursor.execute("SELECT * FROM Scripts  ORDER BY id DESC")
        scripts_user = cursor.fetchall()
        
        # Query to count the tools
        cursor.execute("SELECT COUNT(*) AS count FROM Scripts ")
        scripts_count = cursor.fetchone()['count']
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return scripts_user, scripts_count


def get_script_details_by_user(user_id):
    """Get all scripts from user and their count."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    scripts_user = []
    scripts_count = 0
    
    try:
        # Query to fetch all scripts for the user
        cursor.execute("SELECT * FROM Scripts WHERE user_id=%s ORDER BY id DESC", (user_id,))
        scripts_user = cursor.fetchall()
        
        # Query to count the scripts
        cursor.execute("SELECT COUNT(*) AS count FROM Scripts WHERE user_id=%s", (user_id,))
        scripts_count = cursor.fetchone()['count']
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return scripts_user, scripts_count


def get_titles_for_resource_ids(resource_ids):
    """Get titles for the given resource IDs."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    resource_titles = {}
    
    try:
        # Query to fetch titles for the given resource IDs
        format_strings = ','.join(['%s'] * len(resource_ids))
        cursor.execute(f"SELECT id, title FROM Resources WHERE id IN ({format_strings})", tuple(resource_ids))
        rows = cursor.fetchall()
        
        for row in rows:
            resource_titles[row['id']] = row['title']
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return resource_titles

def add_titles_to_scripts(scripts):
    resource_ids = [script['resource_id'] for script in scripts]
    titles = get_titles_for_resource_ids(resource_ids)
    
    for script in scripts:
        resource_id = script['resource_id']
        script['title'] = titles.get(resource_id, 'Unknown Title')
    
    return scripts



def get_script_details_pendent():
    """Get all tools from user and their count."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    scripts_user = []
    scripts_count = 0
    
    try:
        # Query to fetch all tools
        cursor.execute("SELECT * FROM Scripts WHERE approved='0' ORDER BY id DESC")
        scripts_user = cursor.fetchall()
        
        # Query to count the tools
        cursor.execute("SELECT COUNT(*) AS count FROM Scripts ")
        scripts_count = cursor.fetchone()['count']
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return scripts_user, scripts_count


def get_script_id_by_description(description):
    conn = connect_to_database()  # Connect to the database
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Execute the SQL query to find the script ID by description
        query = "SELECT id FROM Scripts WHERE description = %s"
        cursor.execute(query, (description,))
        result = cursor.fetchone()
        
        # If a result is found, return the script ID
        if result:
            return result['script_id']
        else:
            return None  # Return None if no matching script is found
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


