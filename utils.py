"""
Utility functions for Urban Issue Reporter
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename, allowed_extensions=None):
    """Check if file has allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def send_email_notification(to_email, subject, body, app_config=None):
    """Send email notification"""
    try:
        # Use app config if provided, otherwise use Config class
        if app_config:
            username = app_config['MAIL_USERNAME']
            password = app_config['MAIL_PASSWORD']
            server_name = app_config['MAIL_SERVER']
            port = app_config['MAIL_PORT']
        else:
            username = Config.MAIL_USERNAME
            password = Config.MAIL_PASSWORD
            server_name = Config.MAIL_SERVER
            port = Config.MAIL_PORT
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(server_name, port)
        server.starttls()
        server.login(username, password)
        text = msg.as_string()
        server.sendmail(username, to_email, text)
        server.quit()
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        print(f"📧 Email would have been sent to: {to_email}")
        print(f"📋 Subject: {subject}")
        return False

def generate_welcome_email(name):
    """Generate welcome email HTML"""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
        <h2 style="text-align: center; margin-bottom: 30px;">🏙 Welcome to Urban Issue Reporter!</h2>
        <div style="background: white; color: #333; padding: 30px; border-radius: 8px;">
            <p><strong>Hi {name},</strong></p>
            <p>Thank you for joining our community! You can now:</p>
            <ul style="line-height: 1.8;">
                <li>🚨 Report urban issues in your area</li>
                <li>📍 Use GPS to mark exact locations</li>
                <li>📷 Upload photos of problems</li>
                <li>💬 Engage with your community</li>
                <li>👍 Support important issues with upvotes</li>
            </ul>
            <p style="margin-top: 30px;"><strong>Together, we can make our city better! 🌟</strong></p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://localhost:5000" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Start Reporting Issues</a>
            </div>
        </div>
        <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">Best regards,<br>Urban Issue Reporter Team</p>
    </div>
    """

def generate_issue_report_email(user_name, title, category, priority, address, issue_id):
    """Generate issue report confirmation email HTML"""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
        <h2 style="text-align: center; margin-bottom: 30px;">📋 Issue Reported Successfully!</h2>
        <div style="background: white; color: #333; padding: 30px; border-radius: 8px;">
            <p><strong>Hi {user_name},</strong></p>
            <p>Your issue has been reported and assigned ID: <strong style="color: #667eea;">#{issue_id}</strong></p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">Issue Details:</h3>
                <p><strong>📌 Title:</strong> {title}</p>
                <p><strong>📂 Category:</strong> {category.title()}</p>
                <p><strong>⚡ Priority:</strong> {priority.title()}</p>
                <p><strong>📍 Location:</strong> {address}</p>
            </div>
            <p><strong>Our team will review your report and update you on the progress. 🚀</strong></p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://localhost:5000/issue/{issue_id}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Your Issue</a>
            </div>
        </div>
        <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">Thank you for helping make our city better!<br>Urban Issue Reporter Team</p>
    </div>
    """

def generate_comment_email(reporter_name, issue_title, commenter_name, comment_content, issue_id, is_official=False):
    """Generate comment notification email HTML"""
    comment_type = "Official Response" if is_official else "New Comment"
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
        <h2 style="text-align: center; margin-bottom: 30px;">💬 {comment_type} on Your Issue!</h2>
        <div style="background: white; color: #333; padding: 30px; border-radius: 8px;">
            <p><strong>Hi {reporter_name},</strong></p>
            <p>There's a new {'official response' if is_official else 'comment'} on your issue: <strong style="color: #667eea;">{issue_title}</strong></p>
            <div style="background: {'#f0f4ff' if is_official else '#f8f9fa'}; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {'#667eea' if is_official else '#ddd'};">
                <p><strong>{commenter_name} {'(Official Response)' if is_official else ''} wrote:</strong></p>
                <p style="font-style: italic; margin: 10px 0;">{comment_content}</p>
            </div>
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://localhost:5000/issue/{issue_id}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Full Discussion</a>
            </div>
        </div>
        <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">Best regards,<br>Urban Issue Reporter Team</p>
    </div>
    """

def generate_status_update_email(reporter_name, issue_title, new_status, comment, issue_id):
    """Generate status update email HTML"""
    status_emojis = {
        'pending': '⏳',
        'in-progress': '🔄',
        'resolved': '✅',
        'rejected': '❌'
    }
    
    status_colors = {
        'pending': '#f39c12',
        'in-progress': '#3498db',
        'resolved': '#27ae60',
        'rejected': '#e74c3c'
    }
    
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
        <h2 style="text-align: center; margin-bottom: 30px;">{status_emojis.get(new_status, '📋')} Issue Status Updated!</h2>
        <div style="background: white; color: #333; padding: 30px; border-radius: 8px;">
            <p><strong>Hi {reporter_name},</strong></p>
            <p>Your issue <strong style="color: #667eea;">"{issue_title}"</strong> has been updated by our team:</p>
            <div style="background: {status_colors.get(new_status, '#f8f9fa')}; color: white; padding: 25px; border-radius: 8px; margin: 25px 0; text-align: center;">
                <h3 style="margin: 0; font-size: 1.5rem;">{status_emojis.get(new_status, '📋')} {new_status.replace('-', ' ').title()}</h3>
            </div>
            {f'<div style="background: #f0f4ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;"><p><strong>Official Comment:</strong></p><p style="font-style: italic;">{comment}</p></div>' if comment else ''}
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://localhost:5000/issue/{issue_id}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">View Issue Details</a>
            </div>
        </div>
        <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">Thank you for helping make our city better! 🌟<br>Urban Issue Reporter Team</p>
    </div>
    """
