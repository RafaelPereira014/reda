from datetime import datetime
import os
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, session, url_for
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def insert_script(resource_id, user_id, selected_anos, selected_disciplinas, selected_dominios, selected_subdominios, selected_conceitos, descricao):
    conn = connect_to_database()
    cursor = conn.cursor()
    current_date = datetime.now()

    try:
        # Insert new script
        script_query = """
            INSERT INTO Scripts (resource_id, description, created_at, updated_at, user_id, operation, approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(script_query, (resource_id, descricao, current_date, current_date, user_id, descricao, False))
        script_id = cursor.lastrowid
        print(f"Inserted script with ID: {script_id}")

        def insert_terms(term_list, taxonomy_slug):
            term_insert_query = """
            INSERT INTO script_terms (script_id, term_id, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            """
            
            def get_or_create_term(term, taxonomy_slug):
                get_term_id_query = """
                    SELECT id FROM Terms WHERE title = %s AND taxonomy_id = (SELECT id FROM Taxonomies WHERE slug = %s)
                """
                cursor.execute(get_term_id_query, (term, taxonomy_slug))
                term_row = cursor.fetchone()
                if term_row:
                    return term_row[0]  # Return existing term_id
                else:
                    # Insert the new term
                    insert_term_query = """
                        INSERT INTO Terms (title, taxonomy_id,created_at,updated_at) 
                        VALUES (%s, (SELECT id FROM Taxonomies WHERE slug = %s),NOW(),NOW())
                    """
                    cursor.execute(insert_term_query, (term, taxonomy_slug))
                    return cursor.lastrowid  # Return the newly inserted term_id
            
            for term in term_list:
                term_id = get_or_create_term(term, taxonomy_slug)
                cursor.execute(term_insert_query, (script_id, term_id))

        # Insert associated terms
        insert_terms(selected_anos, 'anos_resources')
        insert_terms(selected_disciplinas, 'areas_resources')
        insert_terms(selected_dominios, 'dominios_resources')
        insert_terms(selected_subdominios, 'subdominios')
        insert_terms(selected_conceitos, 'hashtags')
        
        # Commit the transaction
        conn.commit()

        return script_id

    except mysql.connector.Error as e:
        # Handle database errors
        print(f"Error inserting script: {e}")
        conn.rollback()
        return None

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()




def update_script(resource_id, script_id, user_id, selected_anos, selected_disciplinas, 
                 selected_dominios, selected_subdominios, selected_conceitos, descricao):
    conn = connect_to_database()
    cursor = conn.cursor()
    current_date = datetime.now()

    try:
        # Update existing script using the script_id
        script_query = """
            UPDATE Scripts 
            SET description = %s, updated_at = %s, user_id = %s, operation = %s, approved = %s
            WHERE resource_id = %s AND id = %s
        """
        cursor.execute(script_query, (descricao, current_date, user_id, descricao, False, resource_id, script_id))
        print(f"Updated script with resource ID: {resource_id} and script ID: {script_id}")
        
        conn.commit()  # Commit after updating the script

        # Define a helper function to update terms
        def update_terms(term_list, taxonomy_slug, script_id):
            # Remove existing terms for the script_id and specific taxonomy
            delete_terms_query = """
                DELETE FROM script_terms 
                WHERE script_id = %s AND term_id IN (
                    SELECT id FROM Terms WHERE taxonomy_id = (SELECT id FROM Taxonomies WHERE slug = %s)
                )
            """
            cursor.execute(delete_terms_query, (script_id, taxonomy_slug))
            conn.commit()  # Commit the delete operation

            # Insert updated terms for the script
            term_insert_query = """
                INSERT INTO script_terms (script_id, term_id, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """
            
            for term in term_list:
                # Fetch term_id from Terms table based on term and taxonomy
                get_term_id_query = """
                    SELECT id FROM Terms WHERE title = %s AND taxonomy_id = (SELECT id FROM Taxonomies WHERE slug = %s)
                """
                cursor.execute(get_term_id_query, (term, taxonomy_slug))
                term_row = cursor.fetchone()

                # If the term doesn't exist, insert it into the `Terms` table
                if not term_row:
                    print(f"Term '{term}' for taxonomy '{taxonomy_slug}' not found. Inserting new term.")

                    # Insert new term into Terms table
                    insert_term_query = """
                        INSERT INTO Terms (title, taxonomy_id, created_at, updated_at)
                        VALUES (%s, (SELECT id FROM Taxonomies WHERE slug = %s), NOW(), NOW())
                    """
                    cursor.execute(insert_term_query, (term, taxonomy_slug))
                    conn.commit()  # Commit the insert operation

                    # Fetch the new term_id
                    cursor.execute(get_term_id_query, (term, taxonomy_slug))
                    term_row = cursor.fetchone()

                # Insert the term_id into script_terms if the term exists
                if term_row:
                    term_id = term_row[0]  # Accessing the first element of the tuple (term_id)
                    cursor.execute(term_insert_query, (script_id, term_id))

            conn.commit()  # Commit after inserting terms

        # Update associated terms using the correct script_id
        update_terms(selected_anos, 'anos_resources', script_id)
        update_terms(selected_disciplinas, 'areas_resources', script_id)
        update_terms(selected_dominios, 'dominios_resources', script_id)
        update_terms(selected_subdominios, 'subdominios', script_id)
        update_terms(selected_conceitos, 'hashtags', script_id)

        # Return the script_id after successful updates
        return script_id

    except mysql.connector.Error as e:
        # Log and rollback if an error occurs
        print(f"Error updating script: {e}")
        conn.rollback()
        return None

    finally:
        # Ensure the cursor and connection are closed
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_script_description(script_id):
    """
    Fetches the description of a script from the Scripts table using the given script_id.

    Args:
        script_id (int): The ID of the script for which the description is to be fetched.

    Returns:
        str: The description of the script if found, otherwise an empty string.
    """
    query = "SELECT operation FROM Scripts WHERE id = %s"
    
    try:
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (script_id,))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Assuming 'description' is the first column in the result
                else:
                    return ''  # Return an empty string if no description is found
    except Exception as e:
        print(f"An error occurred while fetching the script description: {e}")
        return ''  # Return an empty string if there's an error

def delete_resource_and_scripts(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    try:
        # Delete associated scripts first if there's a foreign key constraint
        delete_scripts_query = "DELETE FROM Scripts WHERE resource_id = %s"
        cursor.execute(delete_scripts_query, (resource_id,))

        # Delete the resource
        delete_resource_query = "DELETE FROM Resources WHERE id = %s"
        cursor.execute(delete_resource_query, (resource_id,))
        
        # Commit the transaction
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error deleting resource: {e}")
        raise e  # Re-raise the exception to be caught in the route handler
    finally:
        cursor.close()
        conn.close()
        
def delete_scripts(script_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    try:
        # Delete associated scripts first if there's a foreign key constraint
        delete_scripts_query = "DELETE FROM Scripts WHERE id = %s"
        cursor.execute(delete_scripts_query, (script_id,))

        # Commit the transaction
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error deleting resource: {e}")
        raise e  # Re-raise the exception to be caught in the route handler
    finally:
        cursor.close()
        conn.close()
