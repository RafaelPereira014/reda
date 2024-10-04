from datetime import datetime
import logging
from config import DB_CONFIG  # Import the database configuration
from flask import session
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def get_all_tools():
    """Get all approved resources from the DB."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE type_id='1' AND approvedScientific = 1 AND approvedLinguistic = 1 ORDER BY id DESC")
    tools = cursor.fetchall()
    cursor.close()
    conn.close()
    return tools

def get_tools_from_user(userid, search_term=''):
    """Get all tools from user with optional search term filtering and their count."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    tools_user = []
    tools_count = 0
    
    try:
        if search_term:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id=%s
            AND (title LIKE %s OR description LIKE %s)
            ORDER BY id DESC
            """
            search_term = f"%{search_term}%"
            cursor.execute(query, (userid, 1, search_term, search_term))
        else:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id=%s
            ORDER BY id DESC
            """
            cursor.execute(query, (userid, 1))
        
        tools_user = cursor.fetchall()
        
        if search_term:
            query_count = """
            SELECT COUNT(*) AS count FROM Resources
            WHERE user_id=%s AND type_id=%s
            AND (title LIKE %s OR description LIKE %s)
            """
            cursor.execute(query_count, (userid, 1, search_term, search_term))
        else:
            query_count = """
            SELECT COUNT(*) AS count FROM Resources
            WHERE user_id=%s AND type_id=%s
            """
            cursor.execute(query_count, (userid, 1))
        
        tools_count = cursor.fetchone()['count']
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return tools_user, tools_count




def get_pendent_tools():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE type_id='1' AND approved='0' ORDER BY id DESC")
    pendent_tools = cursor.fetchall()
    cursor.close()
    conn.close()
    return pendent_tools

def get_tools_metadata(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT link FROM Resources WHERE id=%s", (resource_id,))
    
    link = cursor.fetchone()
    
    cursor.fetchall()  # Fetch all remaining rows to clear unread results, even though we expect none.
    
    cursor.close()
    conn.close()
    
    if link:
        return link['link']
    else:
        return None

def get_current_month_tools():
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        data = datetime.now()
        # Get the current year and month
        current_year = data.year
        current_month = data.month
        
        # SQL query to select the count of resources created in the current month
        query = """
            SELECT COUNT(*) AS count FROM Resources 
            WHERE YEAR(created_at) = %s AND MONTH(created_at) = %s AND type_id='1'
        """
        cursor.execute(query, (current_year, current_month))
        
        # Fetch the result (only one row with one column)
        result = cursor.fetchone()
        
        # Extract the count value from the result dictionary
        tools_count = result['count'] if result else 0
        
        logging.info(f"Retrieved {tools_count} tools created in the current month.")
        
        return tools_count
    except Exception as e:
        logging.error(f"Error retrieving tools for the current month: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
        
        
def update_tool(resource_id, titulo, descricao, link, embebed):
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

    
    
    