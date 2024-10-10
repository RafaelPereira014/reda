from aifc import Error
from datetime import datetime, time
import logging
import os
import re
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, session, url_for
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def get_title(resource_id):
    """Get the user ID for the given username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title FROM Resources WHERE id=%s", (resource_id,))
    title = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if title:
        return title['title']
    else:
        return None
    
def get_title(resource_id):
    """Get the user ID for the given username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title FROM Resources WHERE id=%s", (resource_id,))
    title = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if title:
        return title['title']
    else:
        return None

def get_userid(username):
    """Get the user ID for the given username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM Users WHERE name=%s", (username,))
    user = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if user:
        return user['id']
    else:
        return None
    
def get_username(user_id):
    """Get the user ID for the given username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM Users WHERE id=%s", (user_id,))
    username = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if username:
        return username['name']
    else:
        return None

def get_all_resources(page, per_page):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    offset = (page - 1) * per_page

    query = """
        SELECT * FROM Resources WHERE (approvedScientific = 1 AND approvedLinguistic = 1)  AND type_id='2' AND hidden='0'
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, (per_page, offset))
    resources = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return resources

def get_total_resource_count():
    conn = connect_to_database()
    cursor = conn.cursor()
    
    query = "SELECT COUNT(*) FROM Resources where type_id='2'"
    
    cursor.execute(query)
    total_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return total_count


def get_pendent_resources():
    """Get all approved resources from the DB with creator's username."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    # Updated query to include the user's name (creator) by joining the Resources and Users table
    query = """
    SELECT r.*, u.name AS username
    FROM Resources r
    LEFT JOIN Users u ON r.user_id = u.id
    WHERE ((r.approvedScientific = 1 AND r.approvedLinguistic = 0) 
       OR (r.approvedScientific = 0 AND r.approvedLinguistic = 1)
       OR (r.approvedScientific = 0 AND r.approvedLinguistic = 0))
      AND r.type_id = '2'
    ORDER BY r.id DESC
    """

    cursor.execute(query)
    pendent_resources = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return pendent_resources

def update_approvedScientific(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE Resources set approvedScientific=%s where id=%s", (1, resource_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "Scientific approval updated"}

def update_approvedLinguistic(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE Resources set approvedLinguistic=%s where id=%s", (1, resource_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "Linguistic approval updated"}

def get_hidden_resources():
    """Get all approved resources from the DB."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE hidden='1' ORDER BY id DESC")
    hidden_resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return hidden_resources


def get_highlighted_resources():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id,title,description FROM Resources WHERE highlight='1' ORDER BY id DESC")
    highlighted_resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return highlighted_resources

def set_on_highlight_resources(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources SET highlight='1' WHERE id=%s", (resource_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in set_on_highlight_resources: {e}")
        return False

def set_off_highlight_resources(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources SET highlight='0' WHERE id=%s", (resource_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in set_off_highlight_resources: {e}")
        return False


    

def get_highlighted_status_for_resources(resource_ids):
    if not resource_ids:
        return {}

    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    # Convert list of IDs to a comma-separated string
    formatted_ids = ','.join([str(id) for id in resource_ids])

    # Query to get highlighted status for all provided resource IDs
    query = f"""
    SELECT id
    FROM Resources
    WHERE id IN ({formatted_ids}) AND highlight = '1'
    """
    cursor.execute(query)

    # Fetch all results
    highlighted_ids = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert list of dictionaries to a set of highlighted IDs
    highlighted_ids_set = {item['id'] for item in highlighted_ids}

    # Return a dictionary mapping resource ID to its highlighted status
    return {id: (id in highlighted_ids_set) for id in resource_ids}

def get_approved_status_for_resources(resource_ids):
    if not resource_ids:
        return {}

    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    # Convert list of IDs to a comma-separated string
    formatted_ids = ','.join([str(id) for id in resource_ids])

    # Query to get highlighted status for all provided resource IDs
    query = f"""
    SELECT id
    FROM Resources
    WHERE id IN ({formatted_ids}) AND approved = '1'
    """
    cursor.execute(query)

    # Fetch all results
    approved_ids = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert list of dictionaries to a set of highlighted IDs
    approved_ids_set = {item['id'] for item in approved_ids}

    # Return a dictionary mapping resource ID to its highlighted status
    return {id: (id in approved_ids_set) for id in resource_ids}


def get_recent_approved_resources(limit=8):
    """Get the most recent approved resources from the DB."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Resources WHERE approvedScientific = 1 AND approvedLinguistic = 1 AND hidden='0' AND type_id='2' ORDER BY id DESC LIMIT %s", (limit,))
    resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return resources


def get_resources_from_user(userid, search_term=''):
    """Get all resources from user with optional search term filtering."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if search_term:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id='2'
            AND (title LIKE %s OR description LIKE %s)
            ORDER BY id DESC
            """
            search_term = f"%{search_term}%"
            cursor.execute(query, (userid, search_term, search_term))
        else:
            query = """
            SELECT * FROM Resources
            WHERE user_id=%s AND type_id='2'
            ORDER BY id DESC
            """
            cursor.execute(query, (userid,))
        
        resources_user = cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        resources_user = []
    finally:
        cursor.close()
        conn.close()
    
    return resources_user


def get_combined_details(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    try:
        # Query to fetch resource details
        resource_query = """
            SELECT * FROM Resources WHERE id = %s
        """
        cursor.execute(resource_query, (resource_id,))
        resource_details = cursor.fetchone()

        # Query to fetch taxonomy details
        taxonomy_query = """
            SELECT
                rt.resource_id,
                MAX(CASE WHEN tax.title = 'Idiomas' THEN t.title END) AS idiomas_title,
                MAX(CASE WHEN tax.title = 'Formato' THEN t.title END) AS formato_title,
                MAX(CASE WHEN tax.title = 'Modos de utilização' THEN t.title END) AS modo_utilizacao_title,
                MAX(CASE WHEN tax.title = 'Requisitos Técnicos' THEN t.title END) AS requisitos_tecnicos_title,
                MAX(CASE WHEN tax.title = 'Anos de escolaridade' THEN t.title END) AS anos_escolaridade_title
            FROM
                resource_terms rt
            JOIN
                Terms t ON rt.term_id = t.id
            JOIN
                Taxonomies tax ON t.taxonomy_id = tax.id
            WHERE
                rt.resource_id = %s
            GROUP BY
                rt.resource_id;
        """
        cursor.execute(taxonomy_query, (resource_id,))
        taxonomy_details = cursor.fetchone()

        # Query to fetch script IDs, associated taxonomies, and operation
        script_query = """
            SELECT
                Scripts.id AS ScriptId,
                Scripts.resource_id AS ResourceId,
                Scripts.operation AS Operation,
                Scripts.approved AS Approved,
                Scripts.user_id AS UserId,
                Terms.title AS TermTitle,
                Taxonomies.slug AS TaxSlug
            FROM
                Scripts
            LEFT JOIN
                script_terms ON Scripts.id = script_terms.script_id
            LEFT JOIN
                Terms ON script_terms.term_id = Terms.id
            LEFT JOIN
                Taxonomies ON Terms.taxonomy_id = Taxonomies.id
            WHERE
                Scripts.resource_id = %s
            AND
                Taxonomies.slug IN ('macro_areas_resources', 'dominios_resources', 'areas_resources', 'anos_resources', 'subdominios', 'hashtags')
            ORDER BY
                Taxonomies.id ASC, Terms.slug+0 ASC;
        """
        cursor.execute(script_query, (resource_id,))
        script_details = cursor.fetchall()

        # Prepare a dictionary to store scripts grouped by script id and taxonomy slugs
        scripts_by_id = {}
        user_ids = []
        for script in script_details:
            script_id = script['ScriptId']
            user_id = script['UserId']
            tax_slug = script['TaxSlug']
            term_title = script['TermTitle']
            operation = script['Operation']
            approved = script['Approved']

            if script_id not in scripts_by_id:
                scripts_by_id[script_id] = {
                    'operation': operation,
                    'user_id': user_id,
                    'approved': approved,
                    'idiomas': [],
                    'anos_resources': [],
                    'formato': [],
                    'modo_utilizacao': [],
                    'requisitos_tecnicos': [],
                    'anos_escolaridade': [],
                    'areas_resources': [],
                    'dominios_resources': [],
                    'macro_areas': [],
                    'subdominios': [],
                    'hashtags': []
                }
                user_ids.append(user_id)
            scripts_by_id[script_id][tax_slug].append(term_title)

        # Fetch user details associated with the scripts
        user_details = {}
        if user_ids:
            user_query = """
                SELECT u.id AS UserId, u.name AS UserName, u.organization AS UserOrganization
                FROM Users u
                WHERE u.id IN ({})
            """.format(','.join(map(str, user_ids)))
            cursor.execute(user_query)
            user_details = {row['UserId']: {'name': row['UserName'], 'organization': row['UserOrganization']} for row in cursor.fetchall()}

        # Combine all details into a single dictionary
        combined_details = {}
        if resource_details:
            combined_details.update({
                'resource_id': resource_id,
                'title': resource_details['title'],
                'approvedScientific': resource_details['approvedScientific'],
                'approvedLinguistic': resource_details['approvedLinguistic'],
                'hidden': resource_details['hidden'],
                'created_at': resource_details['created_at'],
                'organization': resource_details['organization'],
                'description': resource_details['description'],
                'author': resource_details['author'],
                'user_id': resource_details['user_id'],
                'link': resource_details['link'],
                'embed': resource_details['embed']
            })

        if taxonomy_details:
            combined_details.update({
                'idiomas_title': taxonomy_details.get('idiomas_title'),
                'formato_title': taxonomy_details.get('formato_title'),
                'modo_utilizacao_title': taxonomy_details.get('modo_utilizacao_title'),
                'requisitos_tecnicos_title': taxonomy_details.get('requisitos_tecnicos_title'),
                'anos_escolaridade_title': taxonomy_details.get('anos_escolaridade_title')
            })

        combined_details['scripts_by_id'] = scripts_by_id
        combined_details['user_details'] = user_details

        return combined_details if combined_details else None

    except mysql.connector.Error as e:
        # Handle database errors
        print(f"Error retrieving combined details: {e}")
        return None

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def insert_resource_details(cursor, resource_details):
    resource_insert_query = """
        INSERT INTO Resources 
        (title, slug, description, operation, operation_author, techResources, email, organization, 
        duration, highlight, exclusive, embed, link, author, approved, approvedScientific, approvedLinguistic, 
        status, accepted_terms, created_at, updated_at, deleted_at, user_id, type_id, image_id, hidden)
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    resource_data = (
        resource_details['title'],
        resource_details['slug'],  # Make sure resource_details includes 'slug' key
        resource_details['description'],
        resource_details['operation'],
        resource_details['operation_author'],
        resource_details['techResources'],
        resource_details['email'],
        resource_details['organization'],
        resource_details['duration'],
        resource_details['highlight'],
        resource_details['exclusive'],
        resource_details['embed'],
        resource_details['link'],
        resource_details['author'],
        resource_details['approved'],
        resource_details['approvedScientific'],
        resource_details['approvedLinguistic'],
        resource_details['status'],
        resource_details['accepted_terms'],
        resource_details['created_at'],
        resource_details['updated_at'],
        resource_details['deleted_at'],
        resource_details['user_id'],
        resource_details['type_id'],
        resource_details['image_id'],
        resource_details['hidden']
    )
    cursor.execute(resource_insert_query, resource_data)
    return cursor.lastrowid

def insert_taxonomy_details(cursor, resource_id, taxonomy_details):
    # Call the stored procedure
    cursor.callproc('InsertTaxonomyDetails', [
        resource_id,
        taxonomy_details['idiomas_title'],
        taxonomy_details['formato_title'],
        taxonomy_details['modo_utilizacao_title'],
        taxonomy_details['requisitos_tecnicos_title'],
        taxonomy_details['anos_escolaridade_title']
    ])



def insert_script_details(cursor, resource_id, scripts_by_id):
    for script_data in scripts_by_id.values():
        # Insert into Scripts table without passing the script_id
        script_insert_query = """
            INSERT INTO Scripts (resource_id, operation, approved, user_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        script_data_tuple = (
            resource_id,
            script_data['operation'],
            script_data['approved'],
            script_data['user_id']
        )
        cursor.execute(script_insert_query, script_data_tuple)
        script_id = cursor.lastrowid  # Retrieve the auto-incremented script_id

        # Insert into script_terms (for each taxonomy slug and term title combination)
        for tax_slug, term_titles in script_data.items():
            if tax_slug in ['idiomas', 'anos_resources', 'formato', 'modo_utilizacao', 'requisitos_tecnicos', 'anos_escolaridade', 'areas_resources', 'dominios_resources', 'macro_areas', 'subdominios', 'hashtags']:
                taxonomy_id = get_taxonomy_id_for_slug(tax_slug)
                for term_title in term_titles:
                    term_id = get_term_id_for_title(term_title)
                    if term_id is not None:
                        script_term_insert_query = """
                            INSERT INTO script_terms (script_id, term_id)
                            VALUES (%s, %s)
                        """
                        script_term_data = (script_id, term_id)
                        cursor.execute(script_term_insert_query, script_term_data)



def update_resource_details(cursor, resource_id, resource_details):
    cursor.callproc('UpdateResourceDetails', (
        resource_id,
        resource_details['title'],
        resource_details['slug'],
        resource_details['description'],
        resource_details['operation'],
        resource_details['operation_author'],
        resource_details['organization'],
        resource_details['author'],
        resource_details['link'],
        resource_details['embed'],
        resource_details['updated_at'],
        resource_details['user_id'],
        resource_details['type_id'],
        resource_details['image_id']    
        ))

    return cursor.lastrowid

def get_term_id_for_title(term_title, taxonomy_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM Terms
        WHERE title = %s AND taxonomy_id = %s
    """, (term_title, taxonomy_id))
    result = cursor.fetchone()
    cursor.fetchall()  # Fetch any remaining results
    cursor.close()
    conn.close()
    return result[0] if result else None





def update_taxonomy_details(cursor, resource_id, idiomas_selected, formatos_selected, use_mode_selected, requirements_selected):
    try:
        print(f"Updating taxonomy details for resource ID: {resource_id}")

        # Step 1: Delete existing term associations for the resource
        cursor.execute("DELETE FROM resource_terms WHERE resource_id = %s", (resource_id,))
        print(f"Deleted existing terms for resource ID: {resource_id}")

        # Define taxonomy IDs
        taxonomy_ids = {
            'Idiomas': 12,
            'Formato': 11,
            'Modos de utilização': 10,
            'Requisitos técnicos': 13
        }

        # Step 2: Insert new term associations
        term_insert_query = "INSERT INTO resource_terms (resource_id, term_id, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())"
        
        taxonomy_details = {
            'Idiomas': idiomas_selected,
            'Formato': formatos_selected,
            'Modos de utilização': use_mode_selected,   
            'Requisitos técnicos': requirements_selected
        }

        for taxonomy_title, term_titles in taxonomy_details.items():
            taxonomy_id = taxonomy_ids.get(taxonomy_title)
            if not taxonomy_id:
                print(f"No taxonomy ID found for taxonomy title: {taxonomy_title}")
                continue
            
            for term_title in term_titles:
                term_id = get_term_id_for_title(term_title, taxonomy_id)
                if term_id:
                    cursor.execute(term_insert_query, (resource_id, term_id))
                    print(f"Inserted term ID {term_id} for resource ID {resource_id}")
                else:
                    print(f"Term ID not found for title: {term_title} with taxonomy ID: {taxonomy_id}")

    except Exception as e:
        print(f"Error updating taxonomy details: {e}")
        raise

def insert_app_details(cursor, resource_details):
    resource_insert_query = """
        INSERT INTO Resources 
        (title, slug, description, highlight,exclusive, embed, link, approved,author, approvedScientific, approvedLinguistic, 
        status, accepted_terms, hidden, created_at, updated_at, user_id, type_id, image_id)
        VALUES 
        (%s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    resource_data = (
        resource_details['title'],
        resource_details['slug'],
        resource_details['description'],
        resource_details['highlight'],
        resource_details['exclusive'],
        resource_details.get('embed'),  # If 'embed' is not in resource_details, it defaults to None
        resource_details.get('link'),  # If 'link' is not in resource_details, it defaults to None
        resource_details['approved'],
        resource_details['author'],
        resource_details['approvedScientific'],
        resource_details['approvedLinguistic'],
        resource_details['status'],
        resource_details['accepted_terms'],
        resource_details['hidden'],
        resource_details['created_at'],
        resource_details['updated_at'],
        resource_details['user_id'],
        resource_details['type_id'],
        resource_details['image_id']
    )
    cursor.execute(resource_insert_query, resource_data)
    return cursor.lastrowid


def insert_tools_details(cursor, resource_details):
    resource_insert_query = """
        INSERT INTO Resources 
        (title, slug, description, highlight, exclusive, embed, link, approved, approvedScientific, approvedLinguistic, 
        status, accepted_terms, hidden, created_at, updated_at, user_id, type_id, image_id)
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    resource_data = (
        resource_details['title'],
        resource_details['slug'],
        resource_details['description'],
        resource_details['highlight'],
        resource_details['exclusive'],
        resource_details.get('embed'),  # If 'embed' is not in resource_details, it defaults to None
        resource_details.get('link'),  # If 'link' is not in resource_details, it defaults to None
        resource_details['approved'],
        resource_details['approvedScientific'],
        resource_details['approvedLinguistic'],
        resource_details['status'],
        resource_details['accepted_terms'],
        resource_details['hidden'],
        resource_details['created_at'],
        resource_details['updated_at'],
        resource_details['user_id'],
        resource_details['type_id'],
        resource_details['image_id']
    )
    cursor.execute(resource_insert_query, resource_data)
    return cursor.lastrowid

def get_recent_approved_resources_with_details(limit=8):
    """Get the most recent approved resources with combined details."""
    recent_resources = get_recent_approved_resources(limit=limit)
    
    if recent_resources:
        for resource in recent_resources:
            resource['combined_details'] = get_combined_details(resource['id'])
    
    return recent_resources




def no_resources(userid):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS resource_count FROM Resources WHERE user_id=%s", (userid,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

def resource_has_embed_code(resource_slug):
    # Create a database connection
    connection = connect_to_database()
    cursor = connection.cursor()

    try:
        # Query to check if the embed field is NULL
        cursor.execute("SELECT embed FROM Resources WHERE slug = %s", (resource_slug,))
        result = cursor.fetchone()
        
        # Check if the result is None or the embed field is NULL
        return result[0] is not None if result else False
    finally:
        cursor.close()
        connection.close()
        
def get_resource_image_url(resource_slug):
    # Check if the resource has an embed_code
    if resource_has_embed_code(resource_slug):
        return None  # No image if there is an embed_code

    image_extensions = ['png', 'jpg', 'JPG', 'PNG']
    directory_path = os.path.join(current_app.root_path, 'static', 'files', 'resources', resource_slug)

    # Check if the directory for the resource exists
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for ext in image_extensions:
            for filename in os.listdir(directory_path):
                # Check if the filename matches the resource_slug and has the correct extension
                if filename.startswith(resource_slug) and filename.endswith('.' + ext):
                    return url_for('static', filename=f'/files/resources/{resource_slug}/{filename}')

    # If no specific image is found, return the default image
    return url_for('static', filename='images/default.jpg')

def get_resource_files(resource_slug):
    file_extensions = ['pdf', 'docx', 'xlsx','doc']  # Add other file extensions as needed
    directory_path = os.path.join(current_app.root_path, 'static', 'files', 'resources', resource_slug)
    files = []

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for ext in file_extensions:
            for filename in os.listdir(directory_path):
                if filename.startswith(resource_slug) and filename.endswith('.' + ext):
                    file_url = url_for('static', filename=f'/files/resources/{resource_slug}/{filename}')
                    files.append(file_url)

    return files  # Return a list of file URLs


def get_script_files(resource_slug):
    file_extensions = ['pdf', 'docx', 'xlsx','doc']  # Add other file extensions as needed
    directory_path = os.path.join(current_app.root_path, 'static', 'files', 'scripts', resource_slug)
    files = []

    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for ext in file_extensions:
            for filename in os.listdir(directory_path):
                if filename.startswith(resource_slug) and filename.endswith('.' + ext):
                    file_url = url_for('static', filename=f'/files/scripts/{resource_slug}/{filename}')
                    files.append(file_url)

    return files  # Return a list of file URLs

def get_taxonomy_id_for_title(taxonomy_title):
    # Example function to get taxonomy ID from title
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Taxonomies WHERE title = %s", (taxonomy_title,))
    result = cursor.fetchone()
    
    conn.close()
    cursor.close()
    return result[0] if result else None


def get_taxonomy_id_for_slug(slug):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        query = "SELECT id FROM Taxonomies WHERE slug = %s"
        cursor.execute(query, (slug,))
        result = cursor.fetchone()

        if result:
            taxonomy_id = result[0]
            return taxonomy_id
        else:
            print(f"Taxonomy with slug '{slug}' not found.")
            return None

    except mysql.connector.Error as e:
        print(f"Error retrieving taxonomy id for slug '{slug}': {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_term_id(title, taxonomy_title):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    taxonomy_id = get_taxonomy_id_for_title(taxonomy_title)
    if not taxonomy_id:
        print(f"Taxonomy title '{taxonomy_title}' not found")
        return None
    cursor.execute("SELECT id FROM Terms WHERE title = %s AND taxonomy_id = %s", (title, taxonomy_id))
    term = cursor.fetchone()
    return term[0] if term else None


def get_resouce_slug(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT slug FROM Resources WHERE id=%s", (resource_id,))
    slug = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if slug:
        return slug['slug']
    else:
        return None
    
def get_resouce_id(slug):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM Resources WHERE slug=%s", (slug,))
    id = cursor.fetchone()  # fetchone is used because we expect only one user with the given username
    cursor.close()
    conn.close()
    
    if id:
        return id['id']
    else:
        return None

def get_resource_id_for_script(script_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch only once and ensure it's from the right column
    cursor.execute("SELECT resource_id FROM Scripts WHERE id = %s", (script_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        print(f"Fetched resource_id: {row['resource_id']} for script_id: {script_id}")
        return row['resource_id']
    else:
        print(f"No resource_id found for script_id: {script_id}")
        return None
    
def generate_slug(title):
    # Remove special characters and convert spaces to dashes
    slug = re.sub(r'[^\w\s-]', '', title.lower().strip())
    slug = re.sub(r'\s+', '-', slug)
    return slug
    
def get_resource_embed(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT embed FROM Resources WHERE id=%s", (resource_id,))
    embed = cursor.fetchone()  # fetchone is used because we expect only one resource with the given id
    cursor.close()
    conn.close()

    if embed:
        return embed['embed']
    else:
        return None
    

def get_resource_link(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT link FROM Resources WHERE id=%s", (resource_id,))
    link = cursor.fetchone()  # fetchone is used because we expect only one resource with the given id
    cursor.close()
    conn.close()

    if link:
        return link['link']
    else:
        return None

def get_propostasOp(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT operation FROM Scripts WHERE resource_id=%s", (resource_id,))
    operations = cursor.fetchall()  # fetchall is used to get all matching records
    cursor.close()
    conn.close()

    if operations:
        return [operation['operation'] for operation in operations]
    else:
        return []

def search_resources(search_term, page=1, per_page=12):
    search_term = f"%{search_term}%"
    offset = (page - 1) * per_page

    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        # Execute search query with additional conditions for areas_resources, dominios_resources, and subdominios
        query = """
            SELECT SQL_CALC_FOUND_ROWS DISTINCT r.*, r.created_at,
                GROUP_CONCAT(DISTINCT CASE WHEN tx.slug = 'areas_resources' THEN t.title END) AS disciplinas,
                GROUP_CONCAT(DISTINCT CASE WHEN tx.slug = 'dominios_resources' THEN t.title END) AS dominios,
                GROUP_CONCAT(DISTINCT CASE WHEN tx.slug = 'subdominios' THEN t.title END) AS subdominios
            FROM Resources r
            LEFT JOIN Scripts s ON r.id = s.resource_id
            LEFT JOIN script_terms st ON s.id = st.script_id
            LEFT JOIN Terms t ON st.term_id = t.id
            LEFT JOIN Taxonomies tx ON t.taxonomy_id = tx.id
            WHERE (r.title LIKE %s OR r.description LIKE %s OR (tx.slug = 'hashtags' AND t.title LIKE %s)
                OR (tx.slug = 'areas_resources' AND t.title LIKE %s)
                OR (tx.slug = 'dominios_resources' AND t.title LIKE %s)
                OR (tx.slug = 'subdominios' AND t.title LIKE %s))
            AND r.approvedScientific = 1
            AND r.approvedLinguistic = 1
            AND r.hidden = 0
            AND r.type_id='2'
            GROUP BY r.id
            ORDER BY r.id DESC
            LIMIT %s OFFSET %s
        """

        # Add search_term for the additional conditions
        params = (search_term, search_term, search_term, search_term, search_term, search_term, per_page, offset)
        cursor.execute(query, params)
        resources = cursor.fetchall()

        # Execute query to get the total number of results
        cursor.execute("SELECT FOUND_ROWS() AS total_count")
        total_results = cursor.fetchone()["total_count"]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        resources = []
        total_results = 0

    finally:
        cursor.close()
        conn.close()

    return resources, total_results


def advanced_search_resource(ano, disciplina='', dominio='', subdominio='', page=1, per_page=12):
    offset = (page - 1) * per_page

    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        # Base query to filter by `ano`
        query = """
            SELECT SQL_CALC_FOUND_ROWS DISTINCT r.*
            FROM Resources r
            LEFT JOIN Scripts s ON r.id = s.resource_id
            LEFT JOIN script_terms st ON s.id = st.script_id
            LEFT JOIN Terms t ON st.term_id = t.id
            LEFT JOIN Taxonomies tx ON t.taxonomy_id = tx.id
            WHERE tx.slug = 'anos_resources' AND t.title = %s
            AND r.approvedScientific = 1
            AND r.approvedLinguistic = 1
            AND r.hidden = 0
            AND r.type_id='2'
        """
        
        params = [ano]

        # Add filtering by `disciplina` if provided
        if disciplina:
            query += """
            AND EXISTS (
                SELECT 1
                FROM script_terms st2
                JOIN Terms t2 ON st2.term_id = t2.id
                JOIN Taxonomies tx2 ON t2.taxonomy_id = tx2.id
                WHERE st2.script_id = s.id
                AND tx2.slug = 'areas_resources'
                AND t2.title = %s
            )
            """
            params.append(disciplina)

        # Add filtering by `dominio` if provided
        if dominio:
            query += """
            AND EXISTS (
                SELECT 1
                FROM script_terms st3
                JOIN Terms t3 ON st3.term_id = t3.id
                JOIN Taxonomies tx3 ON t3.taxonomy_id = tx3.id
                WHERE st3.script_id = s.id
                AND tx3.slug = 'dominios_resources'
                AND t3.title = %s
            )
            """
            params.append(dominio)

        # Add filtering by `subdominio` if provided
        if subdominio:
            query += """
            AND EXISTS (
                SELECT 1
                FROM script_terms st4
                JOIN Terms t4 ON st4.term_id = t4.id
                JOIN Taxonomies tx4 ON t4.taxonomy_id = tx4.id
                WHERE st4.script_id = s.id
                AND tx4.slug = 'subdominios'
                AND t4.title = %s
            )
            """
            params.append(subdominio)

        # Add ordering and pagination
        query += " ORDER BY r.id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # Execute the query
        cursor.execute(query, params)
        resources = cursor.fetchall()

        # Get the total number of results
        cursor.execute("SELECT FOUND_ROWS() AS total_count")
        total_results = cursor.fetchone()["total_count"]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        resources = []
        total_results = 0

    finally:
        cursor.close()
        conn.close()

    return resources, total_results






def get_current_month_resources():
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        data = datetime.now()
        # Get the current year and month
        current_year = data.year
        current_month = data.month
        
        # SQL query to select count of resources created in the current month
        query = """
            SELECT COUNT(*) AS count FROM Resources 
            WHERE YEAR(created_at) = %s AND MONTH(created_at) = %s
        """
        cursor.execute(query, (current_year, current_month))
        result = cursor.fetchone()
        
        # Extract the count value from the result dictionary
        resources_count = result['count'] if result else 0
        
        logging.info(f"Retrieved {resources_count} resources created in the current month.")
        
        return resources_count
    except Exception as e:
        logging.error(f"Error retrieving resources for the current month: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

        

def get_active_month_users():
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        data = datetime.now()
        # Get the current year and month
        current_year = data.year
        current_month = data.month
        
        query = """
            SELECT user_id, COUNT(*) AS resource_count FROM Resources 
            WHERE YEAR(created_at) = %s AND MONTH(created_at) = %s
            GROUP BY user_id
        """
        cursor.execute(query, (current_year, current_month))
        active_users = cursor.fetchall()
        
        logging.info(f"Retrieved {len(active_users)} active users with resources created in the current month.")
        
        return active_users
    except Exception as e:
        logging.error(f"Error retrieving active users for the current month: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_usernames(user_ids):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        # Prepare the SQL query to retrieve usernames and emails
        query = """
            SELECT id, name, email FROM Users
            WHERE id IN (%s)
        """ % ','.join(['%s'] * len(user_ids))  # Construct the query with the correct number of placeholders
        
        cursor.execute(query, user_ids)
        usernames_and_emails = cursor.fetchall()
        
        logging.info(f"Retrieved {len(usernames_and_emails)} usernames and emails.")
        
        return usernames_and_emails
    except Exception as e:
        logging.error(f"Error retrieving usernames and emails: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_active_users_with_usernames():
    active_users = get_active_month_users()
    if active_users:
        user_ids = [user['user_id'] for user in active_users]
        
        # Retrieve usernames and emails for the user IDs
        usernames_and_emails = get_usernames(user_ids)
        
        # Map user_id to a tuple of (username, email) using the field names from `usernames_and_emails`
        user_id_to_info = {user['id']: (user['name'], user['email']) for user in usernames_and_emails}
        
        # Combine active users with their usernames and emails
        active_users_with_usernames = [
            {
                'id': user['user_id'],  # Ensure consistency with `active_users` key names
                'name': user_id_to_info.get(user['user_id'], ('Unknown', 'Unknown'))[0],
                'email': user_id_to_info.get(user['user_id'], ('Unknown', 'Unknown'))[1],
                'resource_count': user['resource_count']
            }
            for user in active_users
        ]
        
        return active_users_with_usernames
    else:
        return []




def strip_html_tags(text):
    """Remove HTML tags from a string."""
    if not isinstance(text, str):
        return text
    clean = re.compile(r'<.*?>')
    return re.sub(clean, '', text)