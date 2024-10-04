from email import encoders
from email.mime.base import MIMEBase
import logging
import smtplib
import os
import mysql.connector  # Import MySQL Connector Python module
from config import DB_CONFIG  # Import the database configuration
from flask import current_app, session, url_for
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from email.mime.text import MIMEText
from db_operations import *

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def send_email(to_emails, subject, message, attachments=[]):
    try:
        # SMTP server configuration
        smtp_server = 'pegasus.azores.gov.pt'
        smtp_port = 587
        user = 's0204redaproj'
        password = 'JMLpUW7tsA9bgkoq'
        from_email = 'noreply@azores.gov.pt'

        # Create a secure SSL context
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(user, password)

            for to_email in to_emails:
                # Create a MIMEMultipart object to represent the email
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = to_email
                msg['Subject'] = subject

                # Attach the message body
                msg.attach(MIMEText(message, 'html'))

                # Attach files if provided
                for attachment_path in attachments:
                    try:
                        filename = os.path.basename(attachment_path)  # Extract filename from path
                        # Open the file in binary mode
                        with open(attachment_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"',  # Correctly set the filename here
                            )
                            msg.attach(part)
                    except Exception as e:
                        print(f"Failed to attach file {attachment_path}: {e}")

                # Send the email
                server.sendmail(from_email, to_email, msg.as_string())

        print("Emails sent successfully")

    except Exception as e:
        print(f"Failed to send email: {e}")

def send_email_on_resource_create(resource_id, username, resource_link, recipient_emails):
    subject = f"Novo recurso criado #{resource_id}."
    message = f"""
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
            <div class="header">Novo recurso criado <strong>#{resource_id}</strong></div>
            <div class="content">
                <p>Foi adicionado um novo recurso na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)

def send_email_on_app_create(resource_id, username, resource_link, recipient_emails):
    subject = f"Nova aplicação criada #{resource_id}."
    message = f"""
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
            <div class="header">Nova aplicação criada <strong>#{resource_id}</strong></div>
            <div class="content">
                <p>Foi adicionada uma nova aplicação na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)
    
def send_email_on_tool_create(resource_id, username, resource_link, recipient_emails):
    subject = f"Nova ferramenta criada #{resource_id}."
    message = f"""
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
            <div class="header">Nova ferramenta criada <strong>#{resource_id}</strong></div>
            <div class="content">
                <p>Foi adicionada uma nova ferramenta na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)

def send_email_on_resource_update(resource_id, slug, username, resource_link, recipient_emails):
    subject = "Recurso atualizado"
    message = f"""
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
            <div class="header">Recurso atualizado</div>
            <div class="content">
                <p>Foi atualizado o recurso <strong>{slug}</strong> na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)

def send_email_on_app_update(resource_id, slug, username, resource_link, recipient_emails):
    subject = "Aplicação atualizada"
    message = f"""
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
            <div class="header">Aplicação atualizada</div>
            <div class="content">
                <p>Foi atualizada a aplicação <strong>{slug}</strong> na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)
    
def send_email_on_tool_update(resource_id, slug, username, resource_link, recipient_emails):
    subject = "Ferramenta atualizada"
    message = f"""
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
            <div class="header">Ferramenta atualizada</div>
            <div class="content">
                <p>Foi atualizada a ferramenta <strong>{slug}</strong> na plataforma REDA pelo utilizador <strong>{username}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)
    
def send_email_on_script_received(script_id, nomedorecurso, resource_link, recipient_emails):
    subject = "Proposta de operacionalização recebida."
    message = f"""
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
            <div class="header">Proposta de operacionalização recebida</div>
            <div class="content">
                <p>Foi introduzida uma nova proposta de operacionalização no recurso <strong>{nomedorecurso}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)


def send_email_on_script_approval(script_id, nomedorecurso):
    to_email = "user@example.com"  # Fetch the user's email address from the database
    subject = "Proposta de operacionalização aprovada."
    message = f"""
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
            <div class="header">Proposta de operacionalização aprovada</div>
            <div class="content">
                <p>A sua proposta de operacionalização para o recurso {nomedorecurso} foi aprovada.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(to_email, subject, message)


def send_email_on_comment_received(comment_id, slug, resource_link, recipient_emails):
    subject = "Novo comentário recebido."
    message = f"""
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
            <div class="header">Novo comentário recebido</div>
            <div class="content">
                <p>Foi recebido um novo comentário no recurso <strong>{slug}</strong>.</p>
                <p>Pode visualizar os seus detalhes em <a href="{resource_link}">{resource_link}</a>.</p>
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)
    
def send_email_on_speakwus_received(assunto, mensagem, nome, email,recipient_emails):
    subject = "Novo formulário de contacto recebido."
    message = f"""
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
            <div class="header">Novo formulário de contacto recebido</div>
            <div class="content">
                <p>Foi recebida uma nova mensagem no formulário "Fale connosco".</p>
                <p>Nome: {nome} </p>
                <p>Email: {email} </p>
                <p>Assunto:<strong>{assunto}</p>
                <p>Mensagem: {mensagem} </p>
                
            </div>
            <div class="footer">
                <p>Obrigado,<br>A Equipa REDA</p>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(recipient_emails, subject, message)





