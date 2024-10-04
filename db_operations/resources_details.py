from datetime import datetime
from config import DB_CONFIG  # Import the database configuration
from flask import logging, session
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def get_related_resources(resource_title, limit=4):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    try:
        # Split the resource title into keywords
        keywords = resource_title.split()
        
        # Create a LIKE pattern for each keyword
        like_patterns = [f"%{keyword}%" for keyword in keywords]
        
        # Build the query to find related resources
        query = """
            SELECT * FROM Resources
            WHERE  ( 
        """
        
        # Add conditions for each keyword pattern
        query += " OR ".join(["title LIKE %s"] * len(like_patterns))
        
        # Close the WHERE clause and add the conditions and limit
        query += """
            ) AND title != %s AND author IS NOT NULL AND (approvedScientific = 1 AND approvedLinguistic = 1) AND hidden='0' 
            ORDER BY CASE
        """
        
        # Add case for ordering by keyword match count
        for index, keyword in enumerate(keywords):
            query += f" WHEN title LIKE %s THEN {index + 1}"
        
        query += """
            ELSE NULL END
            LIMIT %s
        """
        
        # Prepare the parameters for the query
        query_params = like_patterns + [resource_title] + like_patterns + [limit]
        
        # Execute the query with the patterns and the original title to exclude
        cursor.execute(query, query_params)
        related_resources = cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        related_resources = []
    finally:
        cursor.close()
        conn.close()
    
    return related_resources


def add_comment(resource_id, user_id, text, approved=0, status=1, level=0):
    try:
        # Connect to the database
        conn = connect_to_database()
        cursor = conn.cursor()
        
        # Prepare the SQL query to insert a new comment
        query = """
            INSERT INTO Comments (text, approved, status, level, created_at, updated_at, user_id, resource_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Set the values for the new comment
        values = (
            text,
            approved,
            status,
            level,
            datetime.now(),  # created_at
            datetime.now(),  # updated_at
            user_id,
            resource_id
        )
        
        # Execute the query
        cursor.execute(query, values)
        
        # Commit the transaction
        conn.commit()
        
        # Log success
        print("Comment added successfully.")
        
        return True, None  # Return success
    except Exception as e:
        print(f"Error adding comment: {e}")
        return False, str(e)  # Return failure with error message
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def get_comments_by_resource(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch comments for the given resource ID
        cursor.execute("""
            SELECT c.*, u.name AS user_name
            FROM Comments c
            JOIN Users u ON c.user_id = u.id
            WHERE c.resource_id = %s AND c.approved = 1
            ORDER BY c.created_at DESC
        """, (resource_id,))
        
        comments = cursor.fetchall()
        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_pending_comments():
    try:
        conn = connect_to_database()  # Connect to the database
        cursor = conn.cursor(dictionary=True)
        
        # Fetch comments where `approved` = 0 (pending comments)
        cursor.execute("""
            SELECT c.*, u.name AS user_name, r.title AS resource_title
            FROM Comments c
            JOIN Users u ON c.user_id = u.id
            JOIN Resources r ON c.resource_id = r.id
            WHERE c.approved = 0
            ORDER BY c.created_at DESC
        """)
        
        pending_comments = cursor.fetchall()
        return pending_comments
    except Exception as e:
        print(f"Error fetching pending comments: {e}")
        return []
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the connection
        
        
def approve_comment(comment_id):
    """
    Update the approved state of a comment to approve it.
    
    :param comment_id: The ID of the comment to approve.
    :return: True if the update was successful, False otherwise.
    """
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Update the comment's approved state to 1 (approved)
        cursor.execute("UPDATE Comments SET approved = 1 WHERE id = %s", (comment_id,))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error approving comment: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

