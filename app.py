import datetime
from datetime import date, timedelta
import hashlib
from itertools import islice
from mailbox import Message
import math
import datetime  # Imports the datetime module
import random
import bcrypt
import re
from flask_caching import Cache
from flask import Flask, flash, jsonify, redirect, render_template, request
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import Markup
import mysql.connector
from config import REDIS_CONFIG
from db_operations.resources import *
from db_operations.apps import *
from db_operations.tools import *
from db_operations.resources_details import *
from db_operations.users_op import *
from db_operations.scripts import *
from db_operations.admin import *
from db_operations.new_resource import *
from db_operations.user import *
from db_operations.new_operations import *
from db_operations.notifications import *


app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Needed for session management
UPLOAD_FOLDER = 'static/files/resources/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','doc','pdf','docx'}




# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif','pdf','doc','docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_random_token():
    """Generate a random token."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


# Initialize CSRF Protection
#csrf = CSRFProtect(app)

# Initialize Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    #storage_uri="redis://localhost:6379/0",  # Redis connection URI
    default_limits=["200 per minute"]  # Default rate limit for the entire app
)

app.config.from_mapping(**REDIS_CONFIG)
cache = Cache(app)
connection = mysql.connector.connect(**DB_CONFIG)

admin_emails = get_emails_admins()



@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Apply a custom rate limit specifically for the login route
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        
        if not email or not password:
            error = 'Username and password are required'
            return render_template('login.html', error=error)

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT id, role_id, password FROM Users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            stored_password = user_data[2].encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user_id'] = user_data[0]  # Store user ID in session
                session['user_type'] = user_data[1]  # Store user type in session
                session['welcome_user'] = True  # Set a flag for the welcome message
                session.permanent = True
                return redirect('/')  # Redirect to dashboard on success
            else:
                error = 'Invalid username or password'
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session['bye_message'] = True
    session.clear()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle POST request
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirmPassword = data.get('confirmPassword')
        userType = data.get('userType')

        # Map userType to role_id
        role_id = 3
        if userType == 'colaborador':
            role_id = 4
        elif userType == 'docente':
            role_id = 2
        elif userType == 'outro':
            role_id = 3
        
        if not username or not email or not password or not confirmPassword:
            return jsonify({'success': False, 'message': 'Please fill in all fields'})
        
        if password != confirmPassword:
            return jsonify({'success': False, 'message': 'Passwords do not match'})
        
        success, message = create_user(email, password, username, role_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': message})
    
    # Handle GET request
    return render_template('register.html')

@app.route('/recoverpassword', methods=['GET', 'POST'])
def recoverpassword():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required', 'error')
            return redirect('/recoverpassword')
        
        # Establish a database connection
        conn = connect_to_database()
        cursor = conn.cursor()

        # Retrieve username and user_id from the Users table based on the email
        cursor.execute("SELECT id, name FROM Users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            user_id, username = user_data  # Extract user_id and username
            
            # Generate a secure random token
            token = generate_random_token()
            expiration_time = datetime.utcnow() + timedelta(hours=1)

            # Store the token and expiration time in the database
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO PasswordRecoveryTokens (user_id, token, expiration_time) VALUES (%s, %s, %s)",
                           (user_id, token, expiration_time))
            conn.commit()
            cursor.close()
            conn.close()

            # Create the password reset link
            reset_link = f"http://127.0.0.1:5000/reset_password?token={token}"

            recipients = [email]
            # Send the password recovery email
            send_email_on_password_recovery(username, recipients, reset_link)

            flash('An email has been sent to your address with instructions to reset your password.', 'success')
        else:
            flash('No account found with that email address.', 'error')

        return redirect('/recoverpassword')

    return render_template('recoverpassword.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')  # Get the token from the URL
    if request.method == 'POST':
        new_password = request.form.get('new_password')

        if not new_password:
            flash('New password is required', 'error')
            return redirect(f'/reset_password?token={token}')

        # Verify the token
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM PasswordRecoveryTokens WHERE token = %s AND expiration_time > NOW()", (token,))
        user_data = cursor.fetchone()

        if user_data:
            user_id = user_data[0]

            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # Update the password in the database
            cursor.execute("UPDATE Users SET password = %s WHERE id = %s", (hashed_password, user_id))
            conn.commit()

            # Optionally delete the used token
            cursor.execute("DELETE FROM PasswordRecoveryTokens WHERE token = %s", (token,))
            conn.commit()

            flash('Your password has been reset successfully.', 'success')
            return redirect('/login')
        else:
            flash('Invalid or expired token. Please request a new password recovery email.', 'error')

        cursor.close()
        conn.close()

    return render_template('reset_password.html', token=token)



@app.route('/maintenance')
def maintenance():
    
    return render_template('manutencao.html')

@app.route('/')
def homepage():
    recent_resources = get_recent_approved_resources()
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None
    welcome_message = None


    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    if 'welcome_user' in session:
        welcome_message = 'Bem-vindo(a) à Reda!'
        session.pop('welcome_user')  # Remove the flag after displaying the message
    
    

    # Modify recent_resources to include image_url and embed
    for resource in recent_resources:
        resource['image_url'] = get_resource_image_url(resource['slug'])
        resource['embed'] = get_resource_embed(resource['id'])
        resource['details'] = get_combined_details(resource['id'])  # Fetch resource details
        
        # Identify the oldest script ID and get the areas_resources[0]
        scripts_by_id = resource['details'].get('scripts_by_id', {})
        if scripts_by_id:
            # Find the oldest script ID (minimum ID)
            oldest_script_id = min(scripts_by_id.keys(), key=int)
            oldest_script = scripts_by_id.get(oldest_script_id, {})
            areas_resources = oldest_script.get('areas_resources', [])
            # Determine if there are multiple areas_resources
            if len(areas_resources) > 1:
                resource['areas_resources_display'] = 'Multidisciplinar'
            elif areas_resources:
                resource['areas_resources_display'] = areas_resources[0]
            else:
                resource['areas_resources_display'] = 'No area resources available'
        else:
            resource['areas_resources_display'] = 'No area resources available'

    highlighted_resources = get_highlighted_resources()

    return render_template(
        'index.html', 
        recent_resources=recent_resources, 
        highlighted_resources=highlighted_resources, 
        admin=admin, 
        is_logged_in=is_logged_in  ,
        welcome_message=welcome_message
    )



@app.template_filter('strip_html')
def strip_html_filter(text):
    """Remove HTML tags from a string."""
    return strip_html_tags(text)

app.jinja_env.filters['strip_html'] = strip_html_filter


@app.route('/resources', methods=['GET', 'POST'])
def resources():
    search_term = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 12

    user_id = session.get('user_id')
    is_logged_in = user_id is not None
    admin = is_admin(user_id) if is_logged_in else False
    anos = get_unique_terms(level=1)
    ano = request.args.getlist('anos')  # Change 'ano' to 'anos'
    disciplina = request.args.getlist('disciplinas')  # Change 'disciplina' to 'disciplinas'
    dominio = request.args.getlist('dominios')  
    subdominio = request.args.getlist('subdominios')  
    
    
    
    # If ano is "all", get all anos_resources, otherwise filter by the specific ano
    if ano in ['1º.']:
        disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=None)  # No specific ano, fetch all
    else:
        disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=ano) if ano else []
    # Filter the dominios based on the selected `disciplina`
    dominios = get_filtered_terms(level=3, parent_level=2, parent_term=disciplina) if disciplina else []

    # Filter the subdominios based on the selected `dominio`
    subdominios = get_filtered_terms(level=4, parent_level=3, parent_term=dominio) if dominio else []

    if ano and disciplina:
        paginated_resources, total_resources = advanced_search_resource(ano, disciplina, dominio, subdominio, page, per_page)
    elif ano:
        paginated_resources, total_resources = advanced_search_resource(ano, '', dominio, subdominio, page, per_page)
    elif disciplina:
        paginated_resources, total_resources = advanced_search_resource('', disciplina, dominio, subdominio, page, per_page)
    elif search_term:  # Handle the search terms as a list of terms
        paginated_resources, total_resources = search_resources(search_term, page, per_page)
    else:
        paginated_resources = get_all_resources(page, per_page)
        total_resources = get_total_resource_count()

    total_pages = math.ceil(total_resources / per_page)

    

    for resource in paginated_resources:
        resource['image_url'] = get_resource_image_url(resource['slug'])
        resource['embed'] = get_resource_embed(resource['id'])
        resource['details'] = get_combined_details(resource['id'])

        scripts_by_id = resource['details'].get('scripts_by_id', {})

        if scripts_by_id:
            oldest_script_id = min(scripts_by_id.keys(), key=int)
            oldest_script = scripts_by_id.get(oldest_script_id, {})
            areas_resources = oldest_script.get('areas_resources', [])
            anos_resources = oldest_script.get('anos_resources', [])
            if len(areas_resources) > 1:
                resource['areas_resources_display'] = 'Multidisciplinar'
            elif areas_resources:
                resource['areas_resources_display'] = areas_resources[0]
            else:
                resource['areas_resources_display'] = 'No area resources available'
        else:
            resource['areas_resources_display'] = 'No area resources available'

    if total_pages <= 5:
        page_range = range(1, total_pages + 1)
    else:
        if page <= 3:
            page_range = range(1, 6)
        elif page >= total_pages - 2:
            page_range = range(total_pages - 4, total_pages + 1)
        else:
            page_range = range(page - 2, page + 3)

    return render_template(
        'resources.html',
        all_resources=paginated_resources,
        page=page,
        total_pages=total_pages,
        page_range=page_range,
        search_term=search_term,
        admin=admin,
        total_resources=total_resources,
        is_logged_in=is_logged_in,
        anos=anos,
        disciplinas=disciplinas,
        dominios=dominios,
        subdominios=subdominios,  # Pass the `subdominios` to the template
        ano=ano,
        disciplina=disciplina,
        dominio=dominio,  # Pass the selected `dominio` to the template
        subdominio=subdominio  # Pass the selected `subdominio` to the template
    )
    
@app.route('/resources/details/<int:resource_id>', methods=['GET', 'POST'])
def resource_details(resource_id):
    # Retrieve resource details
    combined_details = get_combined_details(resource_id)
    slug = get_resouce_slug(resource_id)
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    admin = is_admin(user_id) if is_logged_in else False
    
    # Extract combined details
    resource_details = combined_details

    
    
    # Fetch and append additional details
    resource_details['image_url'] = get_resource_image_url(slug)
    resource_details['embed'] = get_resource_embed(resource_id)
    resource_details['files'] = get_resource_files(slug)
    resource_details['link'] = get_resource_link(resource_id)
    resource_details['operations'] = get_propostasOp(resource_id)
    resource_details['username'] = get_username(resource_details['user_id'])
    resource_details['email'] = get_user_email(resource_details['user_id'])

    # Fetch existing comments for the resource
    comments = get_comments_by_resource(resource_id)

    # Fetch related resources and append additional details
    related_resources = get_related_resources(resource_details['title'])
    for related in related_resources:
        related_combined_details = get_combined_details(related['id'])
        if related_combined_details:
            related.update(related_combined_details)
            related_slug = get_resouce_slug(related['id'])
            related['image_url'] = get_resource_image_url(related_slug)
            related['embed'] = get_resource_embed(related['id'])
            related['files'] = get_resource_files(related_slug)
            related['script_files'] = get_script_files(related_slug)
            related['link'] = get_resource_link(related['id'])
            related['operations'] = get_propostasOp(related['id'])
            related['username'] = get_username(related_combined_details['user_id'])

    return render_template('resource_details.html', 
                           resource_details=resource_details, 
                           related_resources=related_resources, 
                           comments=comments,
                           admin=admin,
                           slug=slug,
                           resource_id=resource_id,
                           is_logged_in=is_logged_in)


@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    user_id = session.get('user_id')  # Retrieve user ID from session
    # Check if the user is logged in
    is_logged_in = user_id is not None
    
    if request.method == 'POST' and is_logged_in:
        comment_text = request.form.get('comment')
        resource_id = request.form.get('resource_id')  # Retrieve the resource_id from the form
        if not comment_text or not resource_id:
            return jsonify({"success": False, "error": "Comentário ou recurso não fornecido."})
        
        # Add the comment to the database (assuming a function add_comment exists)
        success, error = add_comment(resource_id=resource_id, user_id=user_id, text=comment_text)
        
        if success:
            return jsonify({"success": True, "message": "Comentário adicionado com sucesso!Está agora a aguardar aprovação"})
        else:
            return jsonify({"success": False, "error": error})
    
    return jsonify({"success": False, "error": "Usuário não está logado."})
        
@app.route('/contact_user', methods=['POST'])
def contact_user():
    user_id = session.get('user_id')  # Retrieve user ID from session
    username = get_username(user_id)
    name = request.form.get('name')
    email = request.form.get('email')
    assunto = request.form.get('assunto')
    
    message = request.form.get('message')
    file = request.files.get('file')

    if not name or not email or not assunto or not message:
        return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios.'})

    try:
        # Define the recipient email addresses
        recipient_emails = [email]  # Add the appropriate recipient emails here
        #recipients=[admin_emails]


        # Prepare the email subject and message
        subject = f"Nova mensagem de {username}: {assunto}"
        email_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .email-container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }}
                .header {{ font-size: 18px; font-weight: bold; color: #333; }}
                .content {{ margin-top: 10px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">Mensagem de {username}</div>
                <div class="content">
                    <p><strong>Assunto:</strong> {assunto}</p>
                    <p><strong>Mensagem:</strong></p>
                    <p>{message}</p>
                </div>
                <div class="footer">
                    <p>Obrigado,<br>A Equipa REDA</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Handle file attachment if present
        attachments = []
        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join('uploads', filename)  # Define your upload path

            if not os.path.exists('uploads'):
                os.makedirs('uploads')

            file.save(file_path)
            attachments.append(file_path)

        # Send the email
        send_email(recipient_emails, subject, email_message, attachments=attachments)

        # Clean up uploaded files
        for attachment in attachments:
            os.remove(attachment)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/hide_resource/<int:resource_id>', methods=['POST'])
def hide_resource_route(resource_id):
    try:
        # Call the function that hides the resource
        hide_resource(resource_id)
        return "Resource hidden successfully", 200
    except Exception as e:
        # Log the error if necessary
        app.logger.error(f"Error hiding resource {resource_id}: {e}")
        return f"Error hiding resource: {e}", 500


@app.route('/delete_resource/<int:resource_id>', methods=['POST'])
def delete_resource(resource_id):
    try:
        # Construct cache key for the resource
        cache_key_areas = f"areas_resources_{resource_id}"
        
        # Delete from cache
        if cache.get(cache_key_areas):
            cache.delete(cache_key_areas)
        
        # Delete resource and its scripts
        delete_resource_and_scripts(resource_id)
        
        # Prepare response
        response = jsonify(message='Resource deleted successfully')
        response.status_code = 200
    except Exception as e:
        # Handle errors
        response = jsonify(message=f'Error occurred: {str(e)}')
        response.status_code = 500
    
    return response

@app.route('/delete_script/<int:script_id>', methods=['POST'])
def delete_script(script_id):
    try:
        delete_scripts(script_id)  # Assuming this function deletes the script based on the script_id
        response = jsonify(success=True, message='Script deleted successfully')  # Include success=True
        response.status_code = 200
    except Exception as e:
        response = jsonify(success=False, message=f'Error occurred: {str(e)}')  # Include success=False
        response.status_code = 500
    
    return response

@app.route('/gerirpropostas/<slug>')
def gerir_propostas(slug):
    
    return render_template('gerirpropostas.html')


@app.route('/novaproposta/<slug>', methods=['GET', 'POST'])
def nova_proposta(slug):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get('user_id')  # Retrieve user ID from session
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    anos = get_unique_terms(level=1)
    resource_id = get_resouce_id(slug)
    
    ano = request.args.get('ano')
    disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=ano) if ano else []
    dominios = []
    subdominios = []
    conceitos = []
    
    
    for disciplina in disciplinas:
        current_dominios = get_filtered_terms(level=3, parent_level=2, parent_term=disciplina) if ano else []
        for dominio in current_dominios:
            current_subdominios = get_filtered_terms(level=4, parent_level=3, parent_term=dominio) if ano else []
            for subdominio in current_subdominios:
                current_conceitos = get_filtered_terms(level=5, parent_level=4, parent_term=subdominio) if ano else []
                conceitos.extend(current_conceitos)
            subdominios.extend(current_subdominios)
        dominios.extend(current_dominios)

    if request.method == 'POST':
        data = request.form
        selected_anos = list(set(data.getlist('anos')))  # Use set to remove duplicates
        selected_disciplinas = list(set(data.getlist('disciplinas')))  # Use set to remove duplicates
        selected_dominios = list(set(data.getlist('dominios')))  # Use set to remove duplicates
        selected_subdominios = list(set(data.getlist('subdominios')))  # Use set to remove duplicates
        selected_conceitos = list(set(data.getlist('conceitos')))
        selected_tags = data.get('keywords').split(',') if data.get('keywords') else []
        descricao = data.get('descricao', '')
        
        insert_script(resource_id, user_id, selected_anos, selected_disciplinas, selected_dominios, selected_subdominios, selected_conceitos, descricao,selected_tags)
        conn.commit()
        recipients=["rafaelpereira0808@gmail.com"]
        #recipients=[admin_emails]

        resource_link = url_for('resource_details', resource_id=resource_id, _external=True)
        #resource_link = "www.google.com"
        send_email_on_script_received(resource_id,slug,resource_link,recipients)
    
        # Redirect to the resource details page
        return redirect(url_for('resource_details', resource_id=resource_id))

    conn.close()
    cursor.close()

    return render_template('novaproposta.html', anos=anos, disciplinas=disciplinas, dominios=dominios, subdominios=subdominios, admin=admin, conceitos=conceitos, slug=slug, resource_id=resource_id,is_logged_in=is_logged_in)


@app.route('/approve_script/<int:script_id>', methods=['POST'])
def approve_script(script_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE Scripts SET approved = '1' WHERE id = %s
        """
        
        cursor.execute(query, (script_id,))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    
    return jsonify(success=success)





@app.route('/resources/edit/<int:resource_id>', methods=['GET', 'POST'])
def resource_edit(resource_id):
    user_id = session.get('user_id')
    is_logged_in = user_id is not None
    admin = is_admin(user_id) if is_logged_in else False
    user = get_username(user_id)
    
    resource_details = get_combined_details(resource_id)
    formatos = get_formatos()
    use_mode = get_modos_utilizacao()
    requirements = get_requisitos_tecnicos()
    idiomas = get_idiomas()

    if not resource_details:
        return render_template('error.html', message='Resource not found'), 404

    if request.method == 'POST':
        title = request.form.get('titulo')
        author = request.form.get('autor')
        organization = request.form.get('organizacao')
        description = request.form.get('descricao')
        idiomas_selected = request.form.getlist('idiomas')
        formatos_selected = request.form.getlist('formato')
        use_mode_selected = request.form.getlist('use_mode')
        requirements_selected = request.form.getlist('requirements')
        slug = generate_slug(title)
        

        # New fields
        link = request.form.get('link')
        embed_code = request.form.get('embed_code')

        imagem = request.files.get('ficheiro')

        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        try:
            # Initialize new_image_id with the existing image_id
            new_image_id = resource_details.get('image_id')
            print(f"Initial new_image_id: {new_image_id}")

            if imagem and allowed_file(imagem.filename):
                # Process new image upload if a new image is provided
                image_filename = imagem.filename
                image_extension = image_filename.rsplit('.', 1)[1].lower()
                random_int = random.randint(1000, 9999)
                new_image_filename = f"{slug}_{random_int}.{image_extension}"
                slug_dir = os.path.join('static', 'files', 'resources', slug)

                if not os.path.exists(slug_dir):
                    os.makedirs(slug_dir)
                image_path = os.path.join(slug_dir, new_image_filename)
                imagem.save(image_path)
                print(f"Image saved to {image_path}")

                # Insert new record into the Files table
                cursor.execute(
                    "INSERT INTO Files (name, extension, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (new_image_filename, image_extension, 1, datetime.now(), datetime.now())
                )
                new_image_id = cursor.lastrowid
                print(f"New image_id after upload: {new_image_id}")

                # Optionally, delete old image file
                old_image_id = resource_details.get('image_id')
                if old_image_id:
                    cursor.execute("SELECT name FROM Files WHERE id = %s", (old_image_id,))
                    old_image = cursor.fetchone()
                    if old_image:
                        old_image_path = os.path.join('static', 'files', 'resources', slug, old_image['name'])
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                            print(f"Old image {old_image_path} deleted")
            else:
                # If no new image is uploaded, retain the old image and update its slug
                if new_image_id:
                    cursor.execute("UPDATE Files SET name = REPLACE(name, %s, %s) WHERE id = %s",
                                   (resource_details['slug'], slug, new_image_id))
                    print(f"Image slug updated for existing image_id: {new_image_id}")

            # Ensure other fields are updated regardless of image update
            if not title or not author or not organization or not description:
                return render_template('edit_resource.html', 
                                       resource_details=resource_details,
                                       formatos=formatos,
                                       use_mode=use_mode,
                                       requirements=requirements,
                                       idiomas=idiomas,
                                       error="All required fields must be filled."), 400

            print(f"Final new_image_id before updating: {new_image_id}")

            resource_details_update = {
                'title': title,
                'slug': slug,
                'description': description,
                'organization': organization,
                'author': author,
                'operation': 'update',
                'operation_author': user,
                'updated_at': datetime.now(),
                'type_id': '2',
                'image_id': new_image_id,  # This will only change if a new image was uploaded
                'link': link,
                'embed': embed_code,
                'user_id': user_id
            }

            update_resource_details(cursor, resource_id, resource_details_update)
            update_taxonomy_details(cursor, resource_id, idiomas_selected, formatos_selected, use_mode_selected, requirements_selected)

            recipients = ["rafaelpereira0808@gmail.com"]
            #recipients=[admin_emails]

            resource_link = url_for('resource_details', resource_id=resource_id, _external=True)
            send_email_on_resource_update(resource_id, slug, user, resource_link, recipients)

            conn.commit()
            print("Resource updated successfully")
            return redirect(url_for('resource_details', resource_id=resource_id))
        except Exception as e:
            conn.rollback()
            print(f"Error updating resource: {e}")
            return render_template('edit_resource.html', 
                                   resource_details=resource_details,
                                   formatos=formatos,
                                   use_mode=use_mode,
                                   requirements=requirements,
                                   idiomas=idiomas,
                                   error=str(e)), 500
        finally:
            cursor.close()
            conn.close()

    formato_title = resource_details.get('formato_title')
    modo_utilizacao_title = resource_details.get('modo_utilizacao_title')
    req_tecnicos_title = resource_details.get('requisitos_tecnicos_title')
    idiomas_title = resource_details.get('idiomas_title')
    
    related_resources = get_related_resources(resource_details['title'])
    
    return render_template(
        'edit_resource.html',
        resource_details=resource_details,
        related_resources=related_resources,
        formatos=formatos,
        use_mode=use_mode,
        requirements=requirements,
        idiomas=idiomas,
        formato_title=formato_title,
        modo_utilizacao_title=modo_utilizacao_title,
        req_tecnicos_title=req_tecnicos_title,
        idiomas_title=idiomas_title,
        admin=admin,
        is_logged_in=is_logged_in
    )


    
@app.route('/resources/edit2/<int:script_id>', methods=['GET', 'POST'])
def resource_edit2(script_id):
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    
    resource_id = get_resource_id_for_script(script_id)
    title = get_title(resource_id)
    slug = generate_slug(title)

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False

    # Get script details
    resource_details = get_combined_details(resource_id)

    # Fetch descricao if available
    initial_description = get_script_description(script_id)  
    print("Initial Description:", initial_description)  # Debugging output
    
    # Fetch all possible anos
    anos = get_unique_terms(level=1)
    keywords = request.form.get('keywords', '').split(',')

    print(f"Received keywords: {keywords}")  # Debugging output

    # Initialize lists for script-specific terms
    selected_anos, selected_disciplinas, selected_dominios, selected_subdominios, selected_conceitos, selected_tags = [], [], [], [], [], []

    if resource_details:
        # Get only the specific script's details
        script = resource_details['scripts_by_id'].get(script_id)
    if script:
        selected_anos = script.get('anos_resources', [])
        selected_disciplinas = script.get('areas_resources', [])
        selected_dominios = script.get('dominios_resources', [])
        selected_subdominios = script.get('subdominios', [])
        selected_conceitos = script.get('hashtags', [])
        selected_tags = script.get('tags_resources', [])
        print(selected_tags)
    else:
        selected_anos, selected_disciplinas, selected_dominios, selected_subdominios, selected_conceitos, selected_tags = [], [], [], [], [], []
    
    # Flatten and remove duplicates for lists (if needed)
    selected_anos = list(set(selected_anos))
    selected_disciplinas = list(set(selected_disciplinas))
    selected_dominios = list(set(selected_dominios))
    selected_subdominios = list(set(selected_subdominios))
    selected_conceitos = list(set(selected_conceitos))
    selected_tags = list(set(selected_tags))

    # Fetch all disciplinas based on the selected anos
    all_disciplinas = set()
    for ano in selected_anos:
        disciplinas_for_ano = get_filtered_terms(level=2, parent_level=1, parent_term=ano)
        all_disciplinas.update(disciplinas_for_ano)
    all_disciplinas = sorted(list(all_disciplinas))

    # Fetch all dominios based on the selected disciplinas
    all_dominios = set()
    for disciplina in selected_disciplinas:
        dominios_for_disciplina = get_filtered_terms(level=3, parent_level=2, parent_term=disciplina)
        all_dominios.update(dominios_for_disciplina)
    all_dominios = sorted(list(all_dominios))

    # Fetch all subdominios based on the selected dominios
    all_subdominios = set()
    for dominio in selected_dominios:
        subdominios_for_dominio = get_filtered_terms(level=4, parent_level=3, parent_term=dominio)
        all_subdominios.update(subdominios_for_dominio)
    all_subdominios = sorted(list(all_subdominios))

    # Fetch all conceitos based on the selected subdominios
    all_conceitos = set()
    for subdominio in selected_subdominios:
        conceitos_for_subdominio = get_filtered_terms(level=5, parent_level=4, parent_term=subdominio)
        all_conceitos.update(conceitos_for_subdominio)
    all_conceitos = sorted(list(all_conceitos))

    if request.method == 'POST':
        data = request.form
        selected_anos = list(set(data.getlist('anos')))
        selected_disciplinas = list(set(data.getlist('disciplinas')))
        selected_dominios = list(set(data.getlist('dominios')))
        selected_subdominios = list(set(data.getlist('subdominios')))
        selected_conceitos = list(set(data.getlist('conceitos')))
        selected_tags = data.get('keywords').split(',') if data.get('keywords') else []
                
        descricao = data.get('descricao', '')  # Fetch updated descricao from form
        print("Submitted Descricao:", descricao)  # Debugging output

        try:
            with connect_to_database() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    # Update the script instead of resource
                    update_script(
                        resource_id, script_id, user_id, selected_anos, selected_disciplinas,
                        selected_dominios, selected_subdominios, selected_conceitos,
                        descricao, selected_tags  # Pass the updated descricao
                    )
                    conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")

        # Redirect to script details instead of resource details
        return redirect(url_for('resource_details', resource_id=resource_id))
    
    # Render the edit page with script data
    return render_template(
        'edit_resource2.html',
        anos=anos, selected_anos=selected_anos, all_disciplinas=all_disciplinas,
        selected_disciplinas=selected_disciplinas, all_dominios=all_dominios, all_conceitos=all_conceitos,
        selected_dominios=selected_dominios, all_subdominios=all_subdominios,
        selected_subdominios=selected_subdominios, selected_conceitos=selected_conceitos, script_id=script_id,
        resource_details=resource_details, admin=admin, is_logged_in=is_logged_in, slug=slug, descricao=initial_description, resource_id=resource_id, selected_tags=selected_tags
    )
@app.route('/apps', methods=['GET'])
def apps():
    user_id = session.get('user_id')  # Retrieve user ID from session
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    page = request.args.get('page', default=1, type=int)
    apps_per_page = 12
    search_query = request.args.get('search', '')

    if search_query:
        # Fetch filtered apps based on search query for the current page
        paginated_apps = get_filtered_apps(search_query, page, apps_per_page)
        total_apps = get_filtered_app_count(search_query)
    else:
        # Fetch all apps for the current page
        paginated_apps = get_all_apps(page, apps_per_page)
        total_apps = get_total_app_count()

    total_pages = (total_apps + apps_per_page - 1) // apps_per_page

    # Update each app with its slug and image URL
    for app in paginated_apps:
        app['slug'] = get_app_slug(app['id'])
        app['metadados'] = get_app_metadata(app['id'])
        if app['slug']:
            app['image_url'] = get_apps_image_url(app['slug'])
        else:
            app['image_url'] = None

    # Define the range of pages to show
    if total_pages <= 5:
        page_range = range(1, total_pages + 1)
    else:
        if page <= 3:
            page_range = range(1, 6)
        elif page >= total_pages - 2:
            page_range = range(total_pages - 4, total_pages + 1)
        else:
            page_range = range(page - 2, page + 3)

    return render_template(
        'apps.html',
        all_apps=paginated_apps,
        page=page,
        total_pages=total_pages,
        page_range=page_range,
        admin=admin,
        search_query=search_query,
        is_logged_in=is_logged_in
    )


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    word = data.get('word')
    results = search_apps(word)
    return jsonify(results)



@app.route('/novaapp', methods=['GET', 'POST'])
def novaapp():
    conn = connect_to_database()
    cursor = conn.cursor()
    user_id = session.get('user_id')  # Retrieve user ID from session
    username = get_username(user_id)  # Fetch the username based on user_id

    print(f"User ID: {user_id}, Username: {username}")  # Debugging output

    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False

    if request.method == 'POST':
        try:
            title = request.form.get('titulo')
            descricao = request.form.get('descricao')
            imagem = request.files.get('ficheiro')
            endereco = request.form.get('endereco')
            embebed = request.form.get('sistema')
            slug = generate_slug(title)

            # Set default image_id to 1
            image_id = 1

            # If there's an image and it's allowed, save it
            if imagem and allowed_file(imagem.filename):
                image_filename = imagem.filename
                image_extension = image_filename.rsplit('.', 1)[1].lower()

                # Generate new file name
                random_int = random.randint(1000, 9999)
                new_image_filename = f"{slug}_{random_int}.{image_extension}"

                # Create the directory /static/files/resources/slug/
                slug_dir = os.path.join('static', 'files', 'apps', slug)
                if not os.path.exists(slug_dir):
                    os.makedirs(slug_dir)

                image_path = os.path.join(slug_dir, new_image_filename)

                # Save the image
                imagem.save(image_path)
                print(f"Image saved to {image_path}")

                # Insert new record into the Files table
                cursor.execute(
                    "INSERT INTO Files (name, extension, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (new_image_filename, image_extension, 1, datetime.now(), datetime.now())
                )
                image_id = cursor.lastrowid  # Update image_id with the newly inserted image's ID

            # Resource details dictionary with the updated or default image_id
            resource_details = {
                'title': title,
                'slug': slug,
                'description': descricao,
                'highlight': '0',
                'exclusive': '0',
                'embed': embebed,
                'link': endereco,
                'approved': '0',
                'author': username,  # Make sure username is correct
                'approvedScientific': '0',
                'approvedLinguistic': '0',
                'status': '0',
                'accepted_terms': '0',
                'hidden': '0',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'user_id': user_id,
                'type_id': '3',
                'image_id': image_id  # Use either the default image ID or the new image ID
            }

            print(f"Resource details before insertion: {resource_details}")  # Debugging output

            resource_id = insert_app_details(cursor, resource_details)
            print(f"Inserted resource ID: {resource_id}")

            conn.commit()
            recipients = ["rafael.b.pereira@azores.gov.pt"]

            resource_link = url_for('apps', resource_id=resource_id, _external=True)
            send_email_on_app_create(resource_id, username, resource_link, recipients)

            return redirect(url_for('apps'))

        except Exception as e:
            print(f"Error in transaction: {str(e)}")
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    return render_template('novaapp.html', admin=admin, is_logged_in=is_logged_in)


@app.route('/resources/edit_app/<int:resource_id>', methods=['GET', 'POST'])
def edit_app(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    user_id = session.get('user_id')  # Retrieve user ID from session
    username = get_username(user_id)
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    title = get_title(resource_id)
    slug = generate_slug(title)
    
    resource_details = get_combined_details(resource_id)
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        link = request.form.get('endereco')
        embebed = request.form.get('sistema')
        print(embebed)
        
        update_app(resource_id, titulo, descricao, link, embebed)
        recipients=["rafaelpereira0808@gmail.com"]
                        #recipients=[admin_emails]

        resource_link = url_for('apps', resource_id=resource_id, _external=True)
        send_email_on_app_update(resource_id,slug,username,resource_link,recipients)
        
        
        
        return redirect(url_for('apps', resource_id=resource_id))
    
    return render_template('edit_app.html', admin=admin, slug=slug, resource_details=resource_details,is_logged_in=is_logged_in)




# Tools
@app.route('/tools', methods=['GET'])
def tools():
    user_id = session.get('user_id')  # Retrieve user ID from session
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    page = request.args.get('page', 1, type=int)
    per_page = 8
    offset = (page - 1) * per_page
    search_query = request.args.get('search', '')  # Retrieve the search query

    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        # Count total number of tools that match the search query for pagination
        cursor.execute(
            "SELECT COUNT(*) as total FROM Resources WHERE type_id=%s AND approvedScientific = 1 AND approvedLinguistic = 1 AND (title LIKE %s OR description LIKE %s)",
            (1, f"%{search_query}%", f"%{search_query}%")
        )
        total_tools = cursor.fetchone()['total']

        # Fetch filtered tools based on the search query for the current page
        cursor.execute(
            "SELECT * FROM Resources WHERE type_id=%s AND approvedScientific = 1 AND approvedLinguistic = 1 AND (title LIKE %s OR description LIKE %s) ORDER BY id DESC LIMIT %s OFFSET %s",
            (1, f"%{search_query}%", f"%{search_query}%", per_page, offset)
        )
    else:
        # Count total number of tools for pagination
        cursor.execute("SELECT COUNT(*) as total FROM Resources WHERE type_id=%s AND approvedScientific = 1 AND approvedLinguistic = 1", (1,))
        total_tools = cursor.fetchone()['total']

        # Fetch tools for the current page
        cursor.execute(
            "SELECT * FROM Resources WHERE type_id=%s AND approvedScientific = 1 AND approvedLinguistic = 1 ORDER BY id DESC LIMIT %s OFFSET %s",
            (1, per_page, offset)
        )

    all_tools = cursor.fetchall()

    # Fetch additional metadata for each tool
    for tool in all_tools:
        tool_id = tool['id']
        tool_metadata = get_tools_metadata(tool_id)
        tool['link'] = tool_metadata

    cursor.close()
    conn.close()

    # Calculate total number of pages
    total_pages = (total_tools + per_page - 1) // per_page

    # Define the range of pages to show
    if total_pages <= 5:
        page_range = range(1, total_pages + 1)
    else:
        if page <= 3:
            page_range = range(1, 6)
        elif page >= total_pages - 2:
            page_range = range(total_pages - 4, total_pages + 1)
        else:
            page_range = range(page - 2, page + 3)

    return render_template(
        'tools.html',
        all_tools=all_tools,
        page=page,
        total_pages=total_pages,
        page_range=page_range,
        admin=admin,
        is_logged_in=is_logged_in,
        search_query=search_query  # Pass the search query to the template
    )



@app.route('/novaferramenta', methods=['GET', 'POST'])
def newtool():
    conn = connect_to_database()
    cursor = conn.cursor()
    user_id = session.get('user_id')  # Retrieve user ID from session
    username=get_username(user_id)
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False

    if request.method == 'POST':
        try:
            title = request.form.get('titulo')
            print(title)
            descricao = request.form.get('descricao')
            print(descricao)
            
            # Retrieving lists of selected items
            endereco = request.form.get('endereco')
            print(endereco)
            embebed = request.form.get('categoria')
            print(embebed)
            slug = generate_slug(title)

            # If there's an image and it's allowed, save it
            

            resource_details = {
                'title': title,
                'slug': slug,
                'description': descricao,
                'highlight': '0',
                'exclusive': '0',
                'embed': embebed,
                'link': endereco,
                'approved': '0',
                'approvedScientific': '0',
                'approvedLinguistic': '0',
                'status': '0',
                'accepted_terms': '0',
                'hidden': '0',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'user_id': user_id,
                'type_id': '1',
                'image_id': '1'
            }

            resource_id = insert_tools_details(cursor, resource_details)
            print(resource_id)

            conn.commit()
            
            recipients=["rafaelpereira0808@gmail.com"]
                            #recipients=[admin_emails]

            resource_link = url_for('tools', resource_id=resource_id, _external=True)
            send_email_on_tool_create(resource_id,username,resource_link,recipients)

            return redirect(url_for('tools'))  # Replace with your target route

        except Exception as e:
            print(f"Error in transaction: {str(e)}")
            conn.rollback()
            raise  # Rethrow the exception for debugging purposes

        finally:
            cursor.close()
            conn.close()

    return render_template('novaferramenta.html', admin=admin,is_logged_in=is_logged_in)


@app.route('/resources/edit_tool/<int:resource_id>', methods=['GET', 'POST'])
def edit_tool(resource_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    user_id = session.get('user_id')  # Retrieve user ID from session
    username = get_username(user_id)
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    title = get_title(resource_id)
    slug = generate_slug(title)
    
    resource_details = get_combined_details(resource_id)
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        link = request.form.get('endereco')
        embebed = request.form.get('sistema')
        
        update_tool(resource_id, titulo, descricao, link, embebed)
        recipients=["rafaelpereira0808@gmail.com"]
                        #recipients=[admin_emails]

        resource_link = url_for('tools', resource_id=resource_id, _external=True)
        send_email_on_tool_update(resource_id,slug,username,resource_link,recipients)
        
        return redirect(url_for('tools', resource_id=resource_id))
    
    return render_template('edit_tool.html', admin=admin, slug=slug, resource_details=resource_details,is_logged_in=is_logged_in)


@app.route('/myaccount')
def my_account():
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    admin = is_admin(user_id) if is_logged_in else False

    # Retrieve query parameters
    search_term = request.args.get('search', '').strip()
    disciplina = request.args.get('disciplina', '').strip()

    # Fetch available disciplinas
    disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=None)

    # Cache key to include user, search term, and disciplina
    cache_key_resources = f"user_resources_{user_id}_{search_term}_{disciplina}"
    my_resources = cache.get(cache_key_resources)

    if my_resources is None:
        # Fetch resources based on search term
        my_resources = get_resources_from_user(user_id, search_term)

        # Filter resources by disciplina
        filtered_resources = []
        for resource in my_resources:
            # Cache key for areas_resources
            cache_key_areas = f"areas_resources_{resource['id']}"
            areas_resources = cache.get(cache_key_areas)

            if areas_resources is None:
                # Fetch areas_resources if not cached
                resource_details = get_combined_details(resource['id'])
                scripts_by_id = resource_details.get('scripts_by_id', {})
                areas_resources = list(
                    set(
                        area.strip()
                        for script_data in scripts_by_id.values()
                        for area in script_data.get('areas_resources', [])
                    )
                )
                cache.set(cache_key_areas, areas_resources, timeout=3600)

            resource['areas_resources'] = [str(area) for area in areas_resources]

            # Apply disciplina filter if specified
            if not disciplina or disciplina in resource['areas_resources']:
                filtered_resources.append(resource)

        my_resources = filtered_resources
        cache.set(cache_key_resources, my_resources, timeout=600)

    # Fetch highlighted and approved statuses
    resource_ids = [resource['id'] for resource in my_resources]
    highlighted_resources = get_highlighted_status_for_resources(resource_ids)
    approved_resources = get_approved_status_for_resources(resource_ids)

    for resource in my_resources:
        resource['highlighted'] = highlighted_resources.get(resource['id'], False)
        resource['approved'] = approved_resources.get(resource['id'], False)

    # Pagination logic for resources
    per_page = 10
    page_resources = request.args.get('page_resources', 1, type=int)
    total_resources = len(my_resources)
    total_pages_resources = math.ceil(total_resources / per_page)
    paginated_resources = my_resources[(page_resources - 1) * per_page:page_resources * per_page]

    # Fetch other user details
    apps_user, apps_count = get_apps_from_user(user_id)
    tools_user, tools_count = get_tools_from_user(user_id)
    user_details = get_details(user_id)
    resources_count = len(my_resources)
    scripts_user, scripts_count = get_script_details_by_user(user_id, search_term)
    scripts_user_with_titles = add_titles_to_scripts(scripts_user)

    # Pagination for proposals
    page_proposals = request.args.get('page_proposals', 1, type=int)
    total_proposals = scripts_count
    total_pages_proposals = math.ceil(total_proposals / per_page)
    paginated_proposals = scripts_user[(page_proposals - 1) * per_page:page_proposals * per_page]

    # Pagination for apps
    page_apps = request.args.get('page_apps', 1, type=int)
    total_apps = apps_count
    total_pages_apps = math.ceil(total_apps / per_page)
    paginated_apps = apps_user[(page_apps - 1) * per_page:page_apps * per_page]

    # Pagination for tools
    page_tools = request.args.get('page_tools', 1, type=int)
    total_tools = tools_count
    total_pages_tools = math.ceil(total_tools / per_page)
    paginated_tools = tools_user[(page_tools - 1) * per_page:page_tools * per_page]

    return render_template(
        '/myaccount/my_account.html',
        my_resources=paginated_resources,
        apps_user=paginated_apps,
        tools_user=paginated_tools,
        user_details=user_details,
        resources_count=resources_count,
        scripts_user=paginated_proposals,
        apps_count=apps_count,
        tools_count=tools_count,
        scripts_count=scripts_count,
        page_resources=page_resources,
        total_pages_resources=total_pages_resources,
        page_proposals=page_proposals,
        total_pages_proposals=total_pages_proposals,
        page_apps=page_apps,
        total_pages_apps=total_pages_apps,
        page_tools=page_tools,
        total_pages_tools=total_pages_tools,
        admin=admin,
        search_term=search_term,
        is_logged_in=is_logged_in,
        disciplinas=disciplinas,
        selected_disciplina=disciplina  # Pass selected disciplina to template
    )



@app.route('/myaccount/minhas_propostas')
def minhas_propostas():
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    if not is_logged_in:
        return redirect('/login')

    # Fetch user's scripts (proposals)
    search_term = request.args.get('search', '').strip()
    scripts_user, scripts_count = get_script_details_by_user(user_id, search_term)
    scripts_user_with_titles = add_titles_to_scripts(scripts_user)
    user_details = get_details(user_id)
    # Pagination
    per_page = 10
    # Pagination for proposals
    page_proposals = request.args.get('page_proposals', 1, type=int)
    total_proposals = scripts_count
    total_pages_proposals = math.ceil(total_proposals / per_page)
    paginated_proposals = scripts_user[(page_proposals - 1) * per_page:page_proposals * per_page]

    return render_template(
        'myaccount/my_proposals.html',
        scripts_user=paginated_proposals,
        page_proposals=page_proposals,
        total_pages_proposals=total_pages_proposals,
        search_term=search_term,
        is_logged_in=is_logged_in,
        user_details=user_details
    )


@app.route('/myaccount/minhas_aplicacoes')
def minhas_aplicacoes():
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    if not is_logged_in:
        return redirect('/login')

    # Fetch user's apps
    apps_user, apps_count = get_apps_from_user(user_id)
    user_details = get_details(user_id)

    # Pagination
    per_page = 10
    # Pagination for apps
    page_apps = request.args.get('page_apps', 1, type=int)
    total_apps = apps_count
    total_pages_apps = math.ceil(total_apps / per_page)
    paginated_apps = apps_user[(page_apps - 1) * per_page:page_apps * per_page]

    return render_template(
        'myaccount/my_apps.html',
        apps_user=paginated_apps,
        page_apps=page_apps,
        user_details=user_details,
        total_pages_apps=total_pages_apps,
        is_logged_in=is_logged_in
    )


@app.route('/myaccount/minhas_ferramentas')
def minhas_ferramentas():
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    if not is_logged_in:
        return redirect('/login')

    # Fetch user's tools
    tools_user, tools_count = get_tools_from_user(user_id)
    user_details = get_details(user_id)

    # Pagination
    per_page = 10
    page_tools = request.args.get('page_tools', 1, type=int)
    total_tools = tools_count
    total_pages_tools = math.ceil(total_tools / per_page)
    paginated_tools = tools_user[(page_tools - 1) * per_page:page_tools * per_page]


    return render_template(
        'myaccount/my_tools.html',
        tools_user=paginated_tools,
        page_tools=page_tools,
        total_pages_tools=total_pages_tools,
        user_details=user_details,
        is_logged_in=is_logged_in
    )
    
@app.route('/myaccount/meu_perfil')
def meu_perfil():
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None
    if not is_logged_in:
        return redirect('/login')


    user_details = get_details(user_id)

    return render_template(
        'myaccount/my_profile.html',
        user_details=user_details,
        is_logged_in=is_logged_in
    )
    
@app.route('/resources/highlight_on/<int:resource_id>', methods=['POST'])
def highlight_on_resource(resource_id):
    success = set_on_highlight_resources(resource_id)
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Failed to highlight resource"}), 500

@app.route('/resources/highlight_off/<int:resource_id>', methods=['POST'])
def highlight_off_resource(resource_id):
    success = set_off_highlight_resources(resource_id)
    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Failed to remove highlight from resource"}), 500





@app.route('/novorecurso', methods=['GET', 'POST'])
def novo_recurso():
    user_id = session.get('user_id')
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    formatos = get_formatos()
    use_mode = get_modos_utilizacao()
    requirements = get_requisitos_tecnicos()
    idiomas = get_idiomas()
    anos = get_anos_escolaridade()

    if request.method == 'POST':
        title = request.form.get('titulo')
        autor = request.form.get('autor')
        org = request.form.get('organizacao')
        descricao = request.form.get('descricao')

        # Retrieving lists of selected items
        idiomas_title = request.form.getlist('idiomas')
        formato_title = request.form.getlist('formato')
        modo_utilizacao_title = request.form.getlist('use_mode')
        requisitos_tecnicos_title = request.form.getlist('requirements')
        anos_escolaridade_title = request.form.getlist('anos')
        endereco = request.form.get('endereco')
        embebed = request.form.get('embebed') or None        
        slug = generate_slug(title)
        duration = request.form.get('duration')

        # Handle file upload if needed
        file = request.files.get('file')
        imagem = request.files.get('ficheiro')

        try:
            conn = connect_to_database()
            cursor = conn.cursor(dictionary=True)

            # Initialize image_id and file_id
            image_id = None
            file_id = None
            
            # If there's a file and it's allowed, save it
            if file and allowed_file(file.filename):
                file_filename = file.filename
                file_extension = file_filename.rsplit('.', 1)[1].lower()

                # Generate new file name
                random_int = random.randint(1000, 9999)
                new_file_filename = f"{slug}_{random_int}.{file_extension}"
                
                
                # Create the directory /static/files/resources/slug/
                slug_dir = os.path.join('static', 'files', 'resources', slug)
                if not os.path.exists(slug_dir):
                    os.makedirs(slug_dir)
                
                file_path = os.path.join(slug_dir, new_file_filename)

                # Save the file
                file.save(file_path)
                print(f"File saved to {file_path}")

                # Insert new record into the Files table
                cursor.execute(
                    "INSERT INTO Files (name, extension, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (new_file_filename, file_extension, 1, datetime.now(), datetime.now())
                )
                file_id = cursor.lastrowid

            # If there's an image and it's allowed, save it
            if imagem and allowed_file(imagem.filename):
                image_filename = imagem.filename
                image_extension = image_filename.rsplit('.', 1)[1].lower()

                # Generate new file name
                random_int = random.randint(1000, 9999)
                new_image_filename = f"{slug}_{random_int}.{image_extension}"
                
                print(slug)
                
                # Create the directory /static/files/resources/slug/
                slug_dir = os.path.join('static', 'files', 'resources', slug)
                if not os.path.exists(slug_dir):
                    os.makedirs(slug_dir)
                
                image_path = os.path.join(slug_dir, new_image_filename)

                # Save the image
                imagem.save(image_path)
                print(f"Image saved to {image_path}")

                # Insert new record into the Files table
                cursor.execute(
                    "INSERT INTO Files (name, extension, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (new_image_filename, image_extension, 1, datetime.now(), datetime.now())
                )
                image_id = cursor.lastrowid
            
            resource_details = {
                'title': title,
                'slug': slug,
                'description': descricao,
                'operation': 'create',
                'operation_author': autor,
                'techResources': None,
                'email': None,
                'organization': org,
                'duration': duration,
                'highlight': 0,
                'exclusive': 0,
                'embed': embebed,
                'link': endereco,
                'author': autor,
                'approved': 0,
                'approvedScientific': 0,
                'approvedLinguistic': 0,
                'status': 1,
                'accepted_terms': 0,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'deleted_at': None,
                'user_id': user_id,
                'type_id': 2,
                'image_id': image_id,  # Use the new image_id
                'hidden': 0
            }

            resource_id = insert_resource_details(cursor, resource_details)

            taxonomy_details = {
                'idiomas_title': idiomas_title[0] if idiomas_title else None,
                'formato_title': formato_title[0] if formato_title else None,
                'modo_utilizacao_title': ', '.join(modo_utilizacao_title) if modo_utilizacao_title else None,
                'requisitos_tecnicos_title': requisitos_tecnicos_title[0] if requisitos_tecnicos_title else None,
                'anos_escolaridade_title': anos_escolaridade_title[0] if anos_escolaridade_title else None,
                'created_at': datetime.now()
            }

            insert_taxonomy_details(cursor, resource_id, taxonomy_details)
            conn.commit()
            # After commit, send the email
            recipients = ["rafaelpereira0808@gmail.com"]
            #                 #recipients=[admin_emails]

            resource_link = url_for('resource_details', resource_id=resource_id, _external=True)
            #resource_link = "www.google.com"
            send_email_on_resource_create(resource_id, autor, resource_link, recipients)
            # print("Email sent successfully after resource creation")
            
            # Store resource_id in session
            session['resource_id'] = resource_id
            return redirect(url_for('novo_recurso2'))  # Replace with your target route

        except Exception as e:
            print(f"Error in transaction: {str(e)}")
            conn.rollback()
            raise  # Rethrow the exception for debugging purposes

        finally:
            cursor.close()
            conn.close()

    return render_template('new_resource.html', formatos=formatos, use_mode=use_mode, requirements=requirements, idiomas=idiomas, anos=anos, admin=admin,is_logged_in=is_logged_in)



@app.route('/novorecurso2', methods=['GET', 'POST'])
def novo_recurso2():
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    user_id = session.get('user_id')  # Retrieve user ID from session
    is_logged_in = user_id is not None  # Check if the user is logged in
    admin = is_admin(user_id) if is_logged_in else False
    anos = get_unique_terms(level=1)
    resource_id = session.get('resource_id')
    titulo = get_title(resource_id)
    slug = generate_slug(titulo)
    autor = get_author(resource_id)

    # Get form data
    if request.method == 'POST':
        data = request.form
        selected_anos = list(set(data.getlist('anos')))  # Get unique selected years
        selected_disciplinas = list(set(data.getlist('disciplinas')))  # Get unique selected subjects (disciplinas)
        selected_dominios = list(set(data.getlist('dominios')))  # Get unique selected domains
        selected_subdominios = list(set(data.getlist('subdominios')))  # Get unique selected subdomains
        print(selected_subdominios)
        selected_conceitos = list(set(data.getlist('conceitos')))  # Get unique selected concepts
        print(selected_conceitos)
        selected_tags = data.get('keywords').split(',') if data.get('keywords') else []  # Get keywords
    
        descricao = data.get('descricao', '')  # Get the description

        # Insert data into the database
        try:
            script_id = insert_script(resource_id, user_id, selected_anos, selected_disciplinas, selected_dominios, selected_subdominios, selected_conceitos, descricao, selected_tags)
            conn.commit()
            print(f"Inserted script with ID: {script_id}")
            # Handle file upload (if provided)
            file = request.files.get('ficheiro')
            if file and allowed_file(file.filename):
                file_filename = file.filename
                file_extension = file_filename.rsplit('.', 1)[1].lower()

                # Process the file upload as described in your code...
            
            # Redirect after processing
            return redirect(url_for('resource_details', resource_id=resource_id))

        except Exception as e:
            print(f"An error occurred: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    
    # Render the page with data for GET request
    return render_template('new_resource2.html', anos=anos, admin=admin, is_logged_in=is_logged_in, resource_id=resource_id)

@app.route('/teste')
def disciplinas_page():
    # Fetch all anos for selection (assuming level 1 are anos)
    anos = get_filtered_terms(level=1, parent_level=None, parent_term=None)
    return render_template('teste.html', anos=anos)

@app.route('/fetch_disciplinas')
def fetch_disciplinas():
    # Fetch selected anos from query parameters
    anos = request.args.get('ano', '').split(';')
 
    # If 'all' is in the anos list, fetch all disciplinas without filtering
    if 'all' in anos:
        disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=None)  # Fetch all disciplinas
    else:
        disciplinas_set = set()
        # Collect all disciplines based on selected anos
        for ano in anos:
            if ano:  # Ensure ano is not empty
                disciplinas_set.update(get_filtered_terms(level=2, parent_level=1, parent_term=ano))
        # Convert the set to a sorted list
        disciplinas = sorted(disciplinas_set)
    return jsonify(disciplinas)

@app.route('/fetch_dominios')
def fetch_dominios():
    # Fetch selected disciplinas from query parameters
    disciplinas = request.args.get('disciplinas', '')
    if disciplinas:
        disciplinas_list = disciplinas.split(';')
        dominios_set = set()
        # Collect all dominios based on selected disciplinas
        for disciplina in disciplinas_list:
            if disciplina:  # Ensure disciplina is not empty
                dominios_set.update(get_filtered_terms(level=3, parent_level=2, parent_term=disciplina))
        # Convert the set to a sorted list
        dominios = sorted(dominios_set)
        return jsonify(dominios)
    # Return an empty list if no disciplinas are provided
    return jsonify([])
 
 
@app.route('/fetch_subdominios')
def fetch_subdominios():
    # Fetch selected dominios from query parameters
    dominios = request.args.get('dominios', '')
    #print("Received Dominios:", dominios)  # Log the received dominios
    if dominios:
        # Split by semicolon instead of comma
        dominios_list = dominios.split(';')
        subdominios_set = set()
        # Collect all subdominios based on selected dominios
        for dominio in dominios_list:
            if dominio:  # Ensure dominio is not empty
                #print(dominio)
                subdominios_set.update(get_filtered_terms(level=4, parent_level=3, parent_term=dominio))
        # Convert the set to a sorted list
        subdominios = sorted(subdominios_set)
       #print(subdominios)
        return jsonify(subdominios)
    # Return an empty list if no dominios are provided
    return jsonify([])
 
@app.route('/fetch_conceitos')
def fetch_conceitos():
    # Fetch selected subdominios from query parameters
    subdominios = request.args.get('subdominios', '')
    if subdominios:
        subdominios_list = subdominios.split(';')
        conceitos_set = set()
 
        # Collect all conceitos based on selected subdominios
        for subdominio in subdominios_list:
            if subdominio:  # Ensure subdominio is not empty
                conceitos_set.update(get_filtered_terms(level=5, parent_level=4, parent_term=subdominio))
        # Convert the set to a sorted list
        conceitos = sorted(conceitos_set)
        return jsonify(conceitos)
    # Return an empty list if no subdominios are provided
    return jsonify([])

@app.route('/fetch_disciplinas_search')
def fetch_disciplinas_search():
    anos = request.args.get('anos', '').split(',')
    anos = [ano for ano in anos if ano]  # Remove any empty values from the list

    app.logger.info(f"Received anos: {anos}")  # Debugging

    if 'all' in anos:
        disciplinas = get_filtered_terms(level=2, parent_level=1, parent_term=None)
    else:
        disciplinas_set = set()
        for ano in anos:
            if ano:
                disciplinas_set.update(get_filtered_terms(level=2, parent_level=1, parent_term=ano))
        disciplinas = sorted(disciplinas_set)

    return jsonify(disciplinas)


@app.route('/fetch_dominios_search')
def fetch_dominios_search():
    # Fetch selected disciplinas from query parameters
    disciplinas = request.args.get('disciplinas', '')
    if disciplinas:
        # Split by comma instead of semicolon
        disciplinas_list = disciplinas.split(',')
        dominios_set = set()
        
        # Collect all dominios based on selected disciplinas
        for disciplina in disciplinas_list:
            if disciplina:  # Ensure disciplina is not empty
                dominios_set.update(get_filtered_terms(level=3, parent_level=2, parent_term=disciplina))
        
        # Convert the set to a sorted list
        dominios = sorted(dominios_set)
        return jsonify(dominios)
    
    # Return an empty list if no disciplinas are provided
    return jsonify([])


@app.route('/fetch_subdominios_search')
def fetch_subdominio_search():
    # Fetch selected dominios from query parameters
    dominios = request.args.get('dominios', '')
    # Log the received dominios for debugging
    app.logger.info(f"Received Dominios: {dominios}")
    
    if dominios:
        # Split by comma instead of semicolon
        dominios_list = dominios.split(',')
        subdominios_set = set()
        
        # Collect all subdominios based on selected dominios
        for dominio in dominios_list:
            if dominio:  # Ensure dominio is not empty
                subdominios_set.update(get_filtered_terms(level=4, parent_level=3, parent_term=dominio))
        
        # Convert the set to a sorted list
        subdominios = sorted(subdominios_set)
        app.logger.info(f"Fetched Subdominios: {subdominios}")
        return jsonify(subdominios)
    
    # Return an empty list if no dominios are provided
    return jsonify([])

@app.route('/fetch_conceitos_search')
def fetch_conceitos_search():
    # Fetch selected subdominios from query parameters
    subdominios = request.args.get('subdominios', '')
    if subdominios:
        subdominios_list = subdominios.split(';')
        conceitos_set = set()

        # Collect all conceitos based on selected subdominios
        for subdominio in subdominios_list:
            if subdominio:  # Ensure subdominio is not empty
                conceitos_set.update(get_filtered_terms(level=5, parent_level=4, parent_term=subdominio))
        
        # Convert the set to a sorted list
        conceitos = sorted(conceitos_set)
        return jsonify(conceitos)
    
    # Return an empty list if no subdominios are provided
    return jsonify([])










# about page
@app.route('/sobre')
def about():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    return render_template('sobre.html',is_logged_in=is_logged_in,admin=admin)

# privacy page 
@app.route('/politica-privacidade')
def privacy():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    return render_template('privacy.html',admin=admin,is_logged_in=is_logged_in)

# help page

@app.route('/ajuda')
def help():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    return render_template('help.html',is_logged_in=is_logged_in,admin=admin)

# ficha tecnica page

@app.route('/fichatecnica')
def fichatecnica():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    return render_template('ficha_tecnica.html',is_logged_in=is_logged_in,admin=admin)

# terms page

@app.route('/termosecondicoes')
def terms():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    return render_template('termosecondicoes.html',is_logged_in=is_logged_in,admin=admin)

# fale connosco

ASSUNTO_MAP = {
    "Opção 1": "Recursos",
    "Opção 2": "Comentários",
    "Opção 3": "Sugestões(endereços)",
    "Opção 4": "Problemas técnicos",
    "Opção 5": "Aplicações",
    "Opção 6": "Registo",
    "Opção 7": "Experimenta",
    "Opção 8": "Outros"
}

@app.route('/faleconnosco', methods=['GET', 'POST'])
def speakwus():
    user_id = session.get('user_id')  # Retrieve user ID from session
    
    # Check if the user is logged in
    is_logged_in = user_id is not None

    # Determine if the user is an admin
    admin = is_admin(user_id) if is_logged_in else False
    selected_assunto = None

    if request.method == 'POST':
        data = request.form
        opcao = data.get('assunto')
        mensagem = data.get('descricao')
        nome = data.get('autor')
        email = data.get('email')
        recipients = ["rafaelpereira0808@gmail.com"]
                        #recipients=[admin_emails]


        # Convert option value to full "assunto" name
        assunto = ASSUNTO_MAP.get(opcao, "Desconhecido")

        # Call the function to send the email
        
        send_email_on_speakwus_received(assunto, mensagem, nome, email, recipients)
        
        # Store the selected "assunto" to display it
        selected_assunto = assunto

    return render_template('faleconnosco.html', selected_assunto=selected_assunto,admin=admin,is_logged_in=is_logged_in)





########---------------------------------_################
# Admin Page
@app.route('/dashboard')
def admin():
    month_names = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
    }
    current_date = datetime.now()
    current_month = month_names[current_date.month]
    active_users = get_active_users_with_usernames()
    monthly_tools = get_current_month_tools()
    monthly_apps = get_current_month_apps()
    monthly_resources = get_current_month_resources()
    monthly_users = get_current_month_users()
    return render_template('admin/admin.html', current_month=current_month,active_users=active_users,monthly_apps=monthly_apps,monthly_tools=monthly_tools,monthly_resources=monthly_resources,monthly_users=monthly_users)  # Pass date to template

@app.route('/dashboard/recursos/pendentes')
def rec_pendentes():
    search_term = request.args.get('search', '')
    recursos_pendentes = get_pendent_resources()

    # Filter resources if a search term is provided
    if search_term:
        recursos_pendentes = [
            resource for resource in recursos_pendentes 
            if search_term.lower() in resource['username'].lower()
        ]
    
    return render_template('admin/recursos/pendentes.html', recursos_pendentes=recursos_pendentes)

@app.route('/update_approved_scientific/<int:resource_id>', methods=['POST'])
def update_approved_scientific(resource_id):
    result = update_approvedScientific(resource_id)
    return jsonify(result)

@app.route('/update_approved_linguistic/<int:resource_id>', methods=['POST'])
def update_approved_linguistic(resource_id):
    result = update_approvedLinguistic(resource_id)
    return jsonify(result)

@app.route('/approve-comment/<int:comment_id>', methods=['POST'])
def approve_comment_route(comment_id):
    """
    Flask route to approve a comment.
    
    :param comment_id: The ID of the comment to approve.
    :return: JSON response indicating success or failure.
    """
    if 'user_id' not in session or not is_admin(session['user_id']):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    success = approve_comment(comment_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to approve comment'}), 500


@app.route('/dashboard/recursos/po/pendentes')
def po_pendentes():
    scripts, scripts_count = get_script_details_pendent()
    
    for script in scripts:
        resource_id = script['resource_id']
        script['title'] = get_title(resource_id)  # Add 'title' key to each script dictionary
        script['author'] = get_username(script['user_id'])
        script['operation'] = get_propostasOp(resource_id)
        

    return render_template('admin/recursos/po_pendentes.html', scripts=scripts, scripts_count=scripts_count)



@app.route('/dashboard/recursos/ocultos')
def hidden():
    ocultos = get_hidden_resources()
    
    return render_template('admin/recursos/ocultos.html',ocultos=ocultos)

@app.route('/resources/show/<int:resource_id>')
def show_resource_route(resource_id):
    result = show_resource(resource_id)
    flash(result)
    return redirect(url_for('hidden'))


@app.route('/dashboard/aplicacoes')
def admin_apps():
    all_apps = get_apps()  # Replace with your function to get all apps
    return render_template('admin/aplicacoes/aplicacoes.html',all_apps=all_apps)

@app.route('/dashboard/aplicacoes/pendentes')
def admin_apps_pendentes():
    pendent_apps = get_pendent_apps()
    return render_template('admin/aplicacoes/pendentes.html',pendent_apps=pendent_apps)

@app.route('/dashboard/ferramentas')
def admin_tools():
    all_tools = get_all_tools()
    return render_template('admin/ferramentas/ferramentas.html',all_tools=all_tools)

@app.route('/dashboard/ferramentas/pendentes')
def admin_tools_pendentes():
    pendent_tools = get_pendent_tools()
    return render_template('admin/ferramentas/pendentes.html',pendent_tools=pendent_tools)

@app.route('/dashboard/comentarios/pendentes')
def admin_comments():
    pendent_comments = get_pending_comments()
    return render_template('admin/comentarios/pendentes.html',pendent_comments=pendent_comments)

@app.route('/dashboard/comentarios/palavras-proibidas')
def admin_comments_prohi():
    bad_words = badwords()
    
    return render_template('admin/comentarios/palavras-proibidas.html',bad_words=bad_words)

#######----- taxonomias-----------####
@app.route('/dashboard/taxonomias')
def admin_taxonomies():
    
    all_taxonomies = taxonomies()
    return render_template('admin/taxonomias/taxonomias.html',all_taxonomies=all_taxonomies)

@app.route('/dashboard/taxonomias/<slug>', methods=['GET', 'POST'])
def admin_edit_taxonomies(slug):
    conn = connect_to_database()
    if conn is None:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    if request.method == 'GET':
        taxonomy_title = get_taxonomy_title(slug)
        taxonomies = edit_taxonomie(slug)
        return render_template('admin/taxonomias/edit_taxonomia.html', taxonomy_title=taxonomy_title, taxonomies=taxonomies, taxonomy_slug=slug)

    elif request.method == 'POST':
        action = request.form.get('action')
        taxonomy_slug = request.form.get('taxonomy_slug')

        term_title = request.form.get('title')
        term_slug = term_title.lower().replace(" ", "-")

        if action == 'add':
            success = insert_term(taxonomy_slug, term_title, term_slug)
            if success:
                return jsonify({"success": True, "message": "Term added successfully"}), 200
            else:
                return jsonify({"success": False, "message": "Failed to add term"}), 500
        
        elif action == 'update':
            term_id = request.form.get('term_id')
            success = update_term(term_id, term_title, term_slug)
            
            return redirect(url_for('admin_edit_taxonomies',slug=slug))
            # if success:
            #     return jsonify({"success": True, "message": "Term updated successfully"}), 200
            # else:
            #     return jsonify({"success": False, "message": "Failed to update term"}), 500

    # This line can be removed, as the only GET request would have already returned.
    # return render_template('admin/taxonomias/edit_taxonomia.html', taxonomy_title=taxonomy_title, taxonomies=taxonomies, taxonomy_slug=slug)





@app.route('/dashboard/taxonomias/relacoes')
def admin_taxonomies_rel():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    relations = taxonomies_relations()
    paginated_relations = list(islice(relations, (page - 1) * per_page, page * per_page))
    
    # Calculate pagination variables
    total_results = len(relations)
    total_pages = math.ceil(total_results / per_page)
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_results': total_results,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None,
        'iter_pages': range(1, total_pages + 1)
    }
    
    return render_template('admin/taxonomias/relacoes.html', relations=paginated_relations, pagination=pagination)

#######----------------####
@app.route('/dashboard/utilizadores')
def admin_users():
    all_users = get_all_users()
    return render_template('admin/utilizadores/utilizadores.html',all_users=all_users)

@app.route('/search-users', methods=['POST'])
def search_users():
    data = request.json
    search_name_email = data.get('searchNameEmail', '').lower()
    user_type = data.get('userType')

    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, email, name, organization, created_at, role_id FROM Users
        WHERE (LOWER(name) LIKE %s OR LOWER(email) LIKE %s)
    """
    params = [f"%{search_name_email}%", f"%{search_name_email}%"]

    if user_type:
        query += " AND role_id = %s"
        params.append(user_type)

    cursor.execute(query, params)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    for user in users:
        if user['role_id'] == 1:
            user['type'] = 'Administrador'
        elif user['role_id'] == 2:
            user['type'] = 'Utilizador Regular'
        elif user['role_id'] == 3:
            user['type'] = 'Convidado'
        else:
            user['type'] = 'Desconhecido'
            
    return jsonify(users)


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=9000)