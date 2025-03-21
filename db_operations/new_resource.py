from datetime import datetime
import os
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, session, url_for
import mysql.connector  # Import MySQL Connector Python module

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def get_formatos():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            t.title AS formato_title
        FROM
            resource_terms rt
        JOIN
            Terms t ON rt.term_id = t.id
        JOIN
            Taxonomies tax ON t.taxonomy_id = tax.id
        WHERE
            tax.title = 'Formato' AND t.title != 'none'
        ORDER BY t.title 
    """)
    formatos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tuple(item['formato_title'] for item in formatos)

def get_idiomas():
    conn = connect_to_database()
    if conn is None:
        return ()  # Return an empty tuple if connection fails
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            t.title AS idiomas_title
        FROM
            Terms t
        JOIN
            Taxonomies tax ON t.taxonomy_id = tax.id
        WHERE
            tax.title = 'Idiomas'
        ORDER BY 
            CASE 
                WHEN t.title = 'Português (PT)' THEN 0
                ELSE 1
            END,
            t.title
    """)
    
    idiomas = cursor.fetchall()
    
    # Filter out None or empty strings
    idiomas_filtered = [item['idiomas_title'] for item in idiomas if item['idiomas_title']]

    cursor.close()
    conn.close()
    
    return tuple(idiomas_filtered)  # Return a tuple without None or empty values

def get_modos_utilizacao():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            t.title AS modo_utilizacao_title
        FROM
            resource_terms rt
        JOIN
            Terms t ON rt.term_id = t.id
        JOIN
            Taxonomies tax ON t.taxonomy_id = tax.id
        WHERE
            tax.title = 'Modos de utilização' AND t.title != 'none'
        ORDER BY t.title
    """)
    modos_utilizacao = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tuple(item['modo_utilizacao_title'] for item in modos_utilizacao)

def get_requisitos_tecnicos():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            t.title AS requisitos_tecnicos_title
        FROM
            resource_terms rt
        JOIN
            Terms t ON rt.term_id = t.id
        JOIN
            Taxonomies tax ON t.taxonomy_id = tax.id
        WHERE
            tax.title = 'Requisitos técnicos' AND t.title!='none'
        ORDER BY t.title
    """)
    requisitos_tecnicos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tuple(item['requisitos_tecnicos_title'] for item in requisitos_tecnicos)

def get_anos_escolaridade():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT
            t.title AS anos_escolaridade_title
        FROM
            resource_terms rt
        JOIN
            Terms t ON rt.term_id = t.id
        JOIN
            Taxonomies tax ON t.taxonomy_id = tax.id
        WHERE
            tax.title = 'Anos escolaridade' AND t.title!='none'
    """)
    anos_escolaridade = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return tuple(item['anos_escolaridade_title'] for item in anos_escolaridade)


def get_unique_terms(level):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    query = f"""
    SELECT DISTINCT
        tx.title AS term_title
    FROM TermRelationships tr
    INNER JOIN terms_relations trs ON trs.term_relationship_id = tr.id
    INNER JOIN Terms tx ON tx.id = trs.term_id
    WHERE trs.level = {level}
    """
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    conn.close()
    return [row['term_title'] for row in result]

def get_filtered_terms(level, parent_level, parent_term):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    # Handle the case when parent_term is None (for "all" case)
    if parent_term is None:
        query = """
        SELECT DISTINCT
            tx.title AS term_title
        FROM terms_relations trs
        INNER JOIN Terms tx ON tx.id = trs.term_id
        WHERE trs.level = %s
        ORDER BY tx.title
        """
        params = [level]
    elif isinstance(parent_term, list) and parent_term:
        # If parent_term is a list, use IN clause
        placeholders = ','.join(['%s'] * len(parent_term))
        query = f"""
        SELECT DISTINCT
            tx.title AS term_title
        FROM terms_relations trs
        INNER JOIN Terms tx ON tx.id = trs.term_id
        WHERE trs.level = %s AND
              trs.term_relationship_id IN (
                  SELECT trs_inner.term_relationship_id
                  FROM terms_relations trs_inner
                  INNER JOIN Terms tx_inner ON tx_inner.id = trs_inner.term_id
                  WHERE trs_inner.level = %s AND tx_inner.title IN ({placeholders})
              )
        ORDER BY tx.title
        """
        params = [level, parent_level] + parent_term  # Flatten list of parent terms
    else:
        # Handle single parent term
        query = """
        SELECT DISTINCT
            tx.title AS term_title
        FROM terms_relations trs
        INNER JOIN Terms tx ON tx.id = trs.term_id
        WHERE trs.level = %s AND
              trs.term_relationship_id IN (
                  SELECT trs_inner.term_relationship_id
                  FROM terms_relations trs_inner
                  INNER JOIN Terms tx_inner ON tx_inner.id = trs_inner.term_id
                  WHERE trs_inner.level = %s AND tx_inner.title = %s
              )
        ORDER BY tx.title
        """
        params = [level, parent_level, parent_term]

    cursor.execute(query, params)
    result = cursor.fetchall()
    
    conn.close()

    return [row['term_title'] for row in result]

def delete_dominio_from_filtered_terms(level, parent_level, parent_term, dominio_title):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Get the filtered terms based on the parent term
    filtered_terms = get_filtered_terms(level, parent_level, parent_term)

    # Check if the domínio exists in the filtered terms
    if dominio_title in filtered_terms:
        # Delete the domínio from the relations
        query = """
        DELETE trs
        FROM terms_relations trs
        INNER JOIN Terms tx ON tx.id = trs.term_id
        INNER JOIN Terms parent_tx ON parent_tx.id = trs.term_relationship_id
        WHERE trs.level = %s AND
              tx.title = %s AND
              parent_tx.title = %s
        """
        cursor.execute(query, (level, dominio_title, parent_term))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()

        return {
            "message": f"'{dominio_title}' deleted successfully from parent '{parent_term}'.",
            "rows_deleted": rows_deleted,
        }
    else:
        conn.close()
        return {
            "message": f"'{dominio_title}' does not exist under parent '{parent_term}'.",
            "rows_deleted": 0,
        }


def create_slug(title):
    return title.replace(" ", "-").lower()

def get_term_id_from_title(title, cursor):
    slug = create_slug(title)
    cursor.execute("SELECT id FROM Terms WHERE slug = %s", (slug,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"Term with title '{title}' not found")

def insert_term_relationships_and_relations(levels_with_titles):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        
        # Step 1: Insert into TermRelationships and get the new id
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO TermRelationships (created_at, updated_at)
            VALUES (%s, %s)
        """, (current_time, current_time))
        term_relationship_id = cursor.lastrowid
        
        # Step 2: Insert each level's terms into terms_relations
        for level, title in levels_with_titles.items():
            term_id = get_term_id_from_title(title, cursor)
            cursor.execute("""
                INSERT INTO terms_relations (level, created_at, updated_at, term_relationship_id, term_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (level, current_time, current_time, term_relationship_id, term_id))
        
        # Commit the transaction
        connection.commit()
        print("New term relationships and relations added successfully")
    
    except mysql.connector.Error as e:
        connection.rollback()
        print(f"Error connecting to MySQL database: {e}")
    
    finally:
        cursor.close()
        connection.close()





