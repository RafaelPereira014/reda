from aifc import Error
from datetime import datetime
import os
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, logging, session, url_for
import mysql.connector  # Import MySQL Connector Python module
import logging

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def taxonomies():
    conn = connect_to_database()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        Taxonomy.id, 
        Taxonomy.title, 
        Taxonomy.slug, 
        Taxonomy.locked, 
        Taxonomy.hierarchical, 
        Taxonomy.created_at, 
        Taxonomy.updated_at, 
        Taxonomy.deleted_at, 
        Taxonomy.type_id, 
        Type.id AS Type_id, 
        Type.title AS Type_title, 
        Type.slug AS Type_slug, 
        Type.created_at AS Type_created_at, 
        Type.updated_at AS Type_updated_at, 
        Type.deleted_at AS Type_deleted_at 
    FROM 
        Taxonomies AS Taxonomy 
    LEFT OUTER JOIN 
        Types AS Type 
    ON 
        Taxonomy.type_id = Type.id 
        AND (Type.deleted_at > NOW() OR Type.deleted_at IS NULL) 
    WHERE 
        (Taxonomy.deleted_at > NOW() OR Taxonomy.deleted_at IS NULL) 
        AND Taxonomy.slug NOT IN ('tags_resources', 'tags_apps', 'tags_tools', 'tags_students') 
    ORDER BY 
        Taxonomy.title ASC;
    """
    
    try:
        cursor.execute(query)
        taxonomies = cursor.fetchall()
        return taxonomies
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        if conn.is_connected():
            conn.close()
            
def edit_taxonomie(taxonomy_slug):
    conn = connect_to_database()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
        Term.id, 
        Term.title, 
        Term.slug, 
        Term.icon, 
        Term.color, 
        Term.type, 
        Term.created_at, 
        Term.updated_at, 
        Term.deleted_at, 
        Term.taxonomy_id, 
        Term.parent_id
    FROM 
        Terms AS Term 
    INNER JOIN 
        Taxonomies AS Taxonomy 
    ON 
        Term.taxonomy_id = Taxonomy.id 
        AND ((Taxonomy.deleted_at > NOW() OR Taxonomy.deleted_at IS NULL) AND Taxonomy.slug = %s) 
    WHERE 
        (Term.deleted_at > NOW() OR Term.deleted_at IS NULL) 
    ORDER BY 
        CAST(Term.title AS UNSIGNED) ASC, 
        Term.title ASC, 
        Term.parent_id ASC ;
    """
    
    try:
        cursor.execute(query, (taxonomy_slug,))
        taxonomies = cursor.fetchall()
        return taxonomies
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        if conn.is_connected():
            conn.close()
            
def update_term(term_id, new_title, new_slug):
    conn = connect_to_database()
    if conn is None:
        return False

    cursor = conn.cursor()

    update_query = """
        UPDATE Terms 
        SET 
            title = %s,
            slug = %s,
            updated_at = NOW()
        WHERE 
            id = %s
    """

    try:
        cursor.execute(update_query, (new_title, new_slug, term_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        if conn.is_connected():
            conn.close()
            
def insert_term(taxonomy_slug, term_title, term_slug, term_parent_id=None):
    conn = connect_to_database()
    if conn is None:
        return False

    cursor = conn.cursor()

    # Retrieve the taxonomy_id based on the taxonomy_slug
    taxonomy_query = "SELECT id FROM Taxonomies WHERE slug = %s AND (deleted_at > NOW() OR deleted_at IS NULL)"
    
    try:
        cursor.execute(taxonomy_query, (taxonomy_slug,))
        result = cursor.fetchone()
        if result is None:
            print(f"Taxonomy with slug '{taxonomy_slug}' not found or is deleted.")
            return False
        taxonomy_id = result[0]

        # Insert the new term into the Terms table
        insert_query = """
            INSERT INTO Terms (title, slug, created_at, updated_at, taxonomy_id, parent_id)
            VALUES (%s, %s, NOW(), NOW(), %s, %s)
        """
        cursor.execute(insert_query, (term_title, term_slug, taxonomy_id, term_parent_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        if conn.is_connected():
            conn.close()




def get_taxonomy_title(slug):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title FROM Taxonomies WHERE slug=%s", (slug,))
    taxonomy_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if taxonomy_data:
        return taxonomy_data['title']
    else:
        return None  # Handle case where taxonomy with given slug is not found
    
def get_distinct_values():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT DISTINCT
        IFNULL(NULLIF(term_slug_order_1, ''), 'N/A') AS anos,
        IFNULL(NULLIF(term_slug_order_2, ''), 'N/A') AS disciplinas,
        IFNULL(NULLIF(term_slug_order_3, ''), 'N/A') AS dominios,
        IFNULL(NULLIF(term_slug_order_4, ''), 'N/A') AS subdominios,
        IFNULL(NULLIF(term_slug_order_5, ''), 'N/A') AS conceitos
    FROM (
        SELECT
            GROUP_CONCAT(IF(trs.level = 1, tx.slug, NULL)) AS term_slug_order_1,
            GROUP_CONCAT(IF(trs.level = 2, tx.slug, NULL)) AS term_slug_order_2,
            GROUP_CONCAT(IF(trs.level = 3, tx.slug, NULL)) AS term_slug_order_3,
            GROUP_CONCAT(IF(trs.level = 4, tx.slug, NULL)) AS term_slug_order_4,
            GROUP_CONCAT(IF(trs.level = 5, tx.slug, NULL)) AS term_slug_order_5
        FROM redav3.TermRelationships tr
        INNER JOIN terms_relations trs ON trs.term_relationship_id = tr.id
        INNER JOIN Terms tx ON tx.id = trs.term_id
        GROUP BY tr.id
    ) AS subquery
    """
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    anos = set()
    disciplinas = set()
    dominios = set()
    subdominios = set()
    conceitos = set()
    
    for row in result:
        if row['anos']:
            anos.update(row['anos'].split(','))
        if row['disciplinas']:
            disciplinas.update(row['disciplinas'].split(','))
        if row['dominios']:
            dominios.update(row['dominios'].split(','))
        if row['subdominios']:
            subdominios.update(row['subdominios'].split(','))
        if row['conceitos']:
            conceitos.update(row['conceitos'].split(','))

    return list(anos), list(disciplinas), list(dominios), list(subdominios), list(conceitos)

def taxonomies_relations(filters=None):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT
        tr.id AS id,
        GROUP_CONCAT(IF(trs.level = 1, tx.title, NULL)) AS term_title_order_1,
        GROUP_CONCAT(IF(trs.level = 1, tx.slug, NULL)) AS term_slug_order_1,
        GROUP_CONCAT(IF(trs.level = 2, tx.title, NULL)) AS term_title_order_2,
        GROUP_CONCAT(IF(trs.level = 2, tx.slug, NULL)) AS term_slug_order_2,
        GROUP_CONCAT(IF(trs.level = 3, tx.title, NULL)) AS term_title_order_3,
        GROUP_CONCAT(IF(trs.level = 3, tx.slug, NULL)) AS term_slug_order_3,
        GROUP_CONCAT(IF(trs.level = 4, tx.title, NULL)) AS term_title_order_4,
        GROUP_CONCAT(IF(trs.level = 4, tx.slug, NULL)) AS term_slug_order_4,
        GROUP_CONCAT(IF(trs.level = 5, tx.title, NULL)) AS term_title_order_5,
        GROUP_CONCAT(IF(trs.level = 5, tx.slug, NULL)) AS term_slug_order_5
    FROM redav3.TermRelationships tr
    INNER JOIN terms_relations trs ON trs.term_relationship_id = tr.id
    INNER JOIN Terms tx ON tx.id = trs.term_id
    """
    
    if filters:
        conditions = []
        if filters.get('ano'):
            conditions.append(f"FIND_IN_SET('{filters['ano']}', GROUP_CONCAT(IF(trs.level = 1, tx.slug, NULL)))")
        if filters.get('disciplina'):
            conditions.append(f"FIND_IN_SET('{filters['disciplina']}', GROUP_CONCAT(IF(trs.level = 2, tx.slug, NULL)))")
        if filters.get('dominio'):
            conditions.append(f"FIND_IN_SET('{filters['dominio']}', GROUP_CONCAT(IF(trs.level = 3, tx.slug, NULL)))")
        if filters.get('subdominio'):
            conditions.append(f"FIND_IN_SET('{filters['subdominio']}', GROUP_CONCAT(IF(trs.level = 4, tx.slug, NULL)))")
        if filters.get('conceito'):
            conditions.append(f"FIND_IN_SET('{filters['conceito']}', GROUP_CONCAT(IF(trs.level = 5, tx.slug, NULL)))")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY tr.id ORDER BY id"
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    conn.close()
    return result


def fetch_users_with_acceptance():
    # Establish connection to the database
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # SQL query to fetch users with acceptance = 1
        query = ("""
            SELECT
                User.id,
                User.name,
                User.email,
                User.organization,
                User.created_at,
                User.updated_at,
                User.status,
                Role.id AS Role_id,
                Role.value AS Role_value,
                Role.type AS Role_type
            FROM
                Users AS User
            INNER JOIN
                Roles AS Role ON User.role_id = Role.id
                AND ((Role.deleted_at > '2024-07-01 15:33:24' OR Role.deleted_at IS NULL)
                     AND Role.status = true)
            WHERE
                (User.acceptance = 1)
                AND ((User.deleted_at > '2024-07-01 15:33:24' OR User.deleted_at IS NULL))
            ORDER BY
                name DESC;
        """)
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch all rows
        users = cursor.fetchall()
        
      
        
        return users
    
    except Error as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()
    
    
def badwords():
    # Establish connection to the database
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # SQL query to fetch users with acceptance = 1
        query = ("""
            SELECT title FROM Badwords AS Badword WHERE ((Badword.deleted_at > '2024-07-01 15:45:24' OR Badword.deleted_at IS NULL) AND Badword.status = true) ORDER BY Badword.title ASC ;
        """)
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch all rows
        badwords = cursor.fetchall()
        
      
        
        return badwords
    
    except Error as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()


def recurso_do_mes(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set highlight='1' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} set as 'Resource of the Month'")
    except Exception as e:
        logging.error(f"Error setting resource {resource_id} as 'Resource of the Month': {e}")
    finally:
        cursor.close()
        conn.close()

def retirar_recurso_do_mes(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set highlight='0' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} removed from 'Resource of the Month'")
    except Exception as e:
        logging.error(f"Error removing resource {resource_id} from 'Resource of the Month': {e}")
    finally:
        cursor.close()
        conn.close()

def recurso_do_mes(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set highlight='1' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} set as 'Resource of the Month'")
        return f"Resource {resource_id} set as 'Resource of the Month'"
    except Exception as e:
        logging.error(f"Error setting resource {resource_id} as 'Resource of the Month': {e}")
        return f"Error setting resource {resource_id} as 'Resource of the Month': {e}"
    finally:
        cursor.close()
        conn.close()

def retirar_recurso_do_mes(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set highlight='0' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} removed from 'Resource of the Month'")
        return f"Resource {resource_id} removed from 'Resource of the Month'"
    except Exception as e:
        logging.error(f"Error removing resource {resource_id} from 'Resource of the Month': {e}")
        return f"Error removing resource {resource_id} from 'Resource of the Month': {e}"
    finally:
        cursor.close()
        conn.close()

def delete_resource(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM Resources where id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} deleted")
        return f"Resource {resource_id} deleted"
    except Exception as e:
        logging.error(f"Error deleting resource {resource_id}: {e}")
        return f"Error deleting resource {resource_id}: {e}"
    finally:
        cursor.close()
        conn.close()

def hide_resource(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set hidden='1' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} hidden")
        return f"Resource {resource_id} hidden"
    except Exception as e:
        logging.error(f"Error hiding resource {resource_id}: {e}")
        return f"Error hiding resource {resource_id}: {e}"
    finally:
        cursor.close()
        conn.close()
        
def show_resource(resource_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE Resources set hidden='0' WHERE id=%s", (resource_id,))
        conn.commit()
        logging.info(f"Resource {resource_id} visible")
        return f"Resource {resource_id} visible"
    except Exception as e:
        logging.error(f"Error showing resource {resource_id}: {e}")
        return f"Error showing resource {resource_id}: {e}"
    finally:
        cursor.close()
        conn.close()

def delete_script(script_id):
    try:
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM Scripts where id=%s", (script_id,))
        conn.commit()
        logging.info(f"Script {script_id} deleted")
        return f"Script {script_id} deleted"
    except Exception as e:
        logging.error(f"Error deleting script {script_id}: {e}")
        return f"Error deleting script {script_id}: {e}"
    finally:
        cursor.close()
        conn.close()