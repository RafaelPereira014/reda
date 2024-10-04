from datetime import datetime
import logging
import os
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, session, url_for
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def get_all_apps(page, apps_per_page):
    offset = (page - 1) * apps_per_page
    query = """
        SELECT * FROM Resources
        WHERE type_id='3' AND approvedScientific = 1 AND approvedLinguistic = 1
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (apps_per_page, offset))
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return apps


def get_apps():
    """Get all approved resources from the DB."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE type_id='3'  ORDER BY id DESC")
    all_apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return all_apps

def get_apps_from_user(userid, search_term=''):
    """Get all apps from user with optional search term filtering and their count."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    apps_user = []
    apps_count = 0
    
    try:
        if search_term:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id=%s
            AND (title LIKE %s OR description LIKE %s)
            ORDER BY id DESC
            """
            search_term = f"%{search_term}%"
            cursor.execute(query, (userid, 3, search_term, search_term))
        else:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id=%s
            ORDER BY id DESC
            """
            cursor.execute(query, (userid, 3))
        
        apps_user = cursor.fetchall()
        
        if search_term:
            query_count = """
            SELECT COUNT(*) AS count FROM Resources
            WHERE user_id=%s AND type_id=%s
            AND (title LIKE %s OR description LIKE %s)
            """
            cursor.execute(query_count, (userid, 3, search_term, search_term))
        else:
            query_count = """
            SELECT COUNT(*) AS count FROM Resources
            WHERE user_id=%s AND type_id=%s
            """
            cursor.execute(query_count, (userid, 3))
        
        apps_count = cursor.fetchone()['count']
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return apps_user, apps_count


def get_pendent_apps():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE type_id='3' AND approved='0' ORDER BY id DESC")
    pendent_apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return pendent_apps

def get_app_slug(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT slug FROM Resources WHERE type_id='3' AND id=%s", (resource_id,))
    slug = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if slug:
        return slug['slug']
    else:
        return None
    
def get_apps_image_url(resource_slug):
    image_extensions = ['png', 'jpg']
    directory_path = os.path.join(current_app.root_path, 'static', 'files', 'apps', resource_slug)

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for ext in image_extensions:
            for filename in os.listdir(directory_path):
                if filename.startswith(resource_slug) and filename.endswith('.' + ext):
                    return url_for('static', filename=f'files/apps/{resource_slug}/{filename}')

    return None  # Return None if no image is found


def get_total_app_count():
    query = """
        SELECT COUNT(*) as count FROM Resources
        WHERE type_id='3'
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['count']

def get_filtered_apps(search_query, page, apps_per_page):
    offset = (page - 1) * apps_per_page
    search_query = f"%{search_query}%"

    query = """
        SELECT * FROM Resources
        WHERE type_id='3' AND (title LIKE %s OR description LIKE %s)
        LIMIT %s OFFSET %s
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (search_query, search_query, apps_per_page, offset))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return result

def get_filtered_app_count(search_query):
    search_query = f"%{search_query}%"

    query = """
        SELECT COUNT(*) as count FROM Resources
        WHERE type_id='3' AND (title LIKE %s OR description LIKE %s)
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (search_query, search_query))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result['count']

def get_filtered_tools(search_query, page, apps_per_page):
    offset = (page - 1) * apps_per_page
    search_query = f"%{search_query}%"

    query = """
        SELECT * FROM Resources
        WHERE type_id='1' AND (title LIKE %s OR description LIKE %s)
        LIMIT %s OFFSET %s
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (search_query, search_query, apps_per_page, offset))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return result


def get_filtered_tool_count(search_query):
    search_query = f"%{search_query}%"

    query = """
        SELECT COUNT(*) as count FROM Resources
        WHERE type_id='1' AND (title LIKE %s OR description LIKE %s)
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (search_query, search_query))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result['count']

def get_app_metadata(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT metadata FROM resource_terms WHERE resource_id=%s", (resource_id,))
    
    metadata = cursor.fetchone()
    
    cursor.fetchall()  # Fetch all remaining rows to clear unread results, even though we expect none.
    
    cursor.close()
    conn.close()
    
    if metadata:
        return metadata['metadata']
    else:
        return None


def search_apps(word):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    # Ensure the query parameter includes wildcards for proper search functionality
    search_word = f"%{word}%"
    
    try:
        cursor.execute("SELECT * FROM Resources WHERE type_id='3' AND title LIKE %s", (search_word,))
        search_apps = cursor.fetchall()  # Fetch all matching rows
        
        return search_apps if search_apps else None
        
    except Exception as e:
        print(f"Error executing search query: {e}")
        return None
        
    finally:
        cursor.close()
        conn.close()

def get_current_month_apps():
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        data = datetime.now()
        # Get the current year and month
        current_year = data.year
        current_month = data.month
        
        # SQL query to select count of apps created in the current month
        query = """
            SELECT COUNT(*) AS count FROM Resources 
            WHERE YEAR(created_at) = %s AND MONTH(created_at) = %s AND type_id='3'
        """
        cursor.execute(query, (current_year, current_month))
        result = cursor.fetchone()
        
        # Extract the count value from the result dictionary
        apps_count = result['count'] if result else 0
        
        logging.info(f"Retrieved {apps_count} apps created in the current month.")
        
        return apps_count
    except Exception as e:
        logging.error(f"Error retrieving apps for the current month: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



def update_app(resource_id, titulo, descricao, link, embebed):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    query = """
        UPDATE Resources
        SET title = %s,
            description = %s,
            link = %s,
            embed = %s
        WHERE id = %s
    """
    cursor.execute(query, (titulo, descricao, link, embebed, resource_id))
    conn.commit()
    
    cursor.close()
    conn.close()