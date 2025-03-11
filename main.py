import os
import math
import re
import secrets
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import ( JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token, )
from flask_bcrypt import Bcrypt , check_password_hash, generate_password_hash
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from models import Contacts,User,Posts,db

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.secret_key)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Database Configuration
local_server = os.getenv('LOCAL_SERVER', 'True').lower() == 'true'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LOCAL_URL') if local_server else os.getenv('PROD_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# File upload configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/assets/upload/profile")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('GMAIL_USER')
mail = Mail(app)

# Blog Configurations
blog_name = os.getenv('BLOG_NAME', 'Code Hunter')
about_txt = os.getenv('ABOUT_TXT', 'About me section')
no_of_posts = int(os.getenv('NO_OF_POSTS', '3'))

# Social Media URLs
fb_url = os.getenv('FB_URL', 'https://www.facebook.com/code_hunter')
x_url = os.getenv('X_URL', 'https://x.com/code_hunter')
git_url = os.getenv('GIT_URL', 'https://github.com/code_hunter')

# Helper function for file validation
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

with app.app_context():
    db.create_all()

# User Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        # Handle JSON data
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip()
        place = request.form.get('place', '').strip()
        address = request.form.get('address', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        file = request.files.get('image')
        
        # Validation errors
        errors = {}

        if not name:
            errors['name'] = "Name is required"
        elif not re.match(r"^[A-Za-z\s]+$", name):
            errors['name'] = "Name must contain only letters and spaces"

        if not dob:
            errors['dob'] = "Date of birth is required"
        
        if not place:
            errors['place'] = "Place is required"
        
        if not address:
            errors['address'] = "Address is required"
        
        if not email:
            errors['email'] = "Email is required"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors['email'] = "Invalid email format"
        elif User.query.filter_by(email=email).first():
            errors['email'] = "Email already registered"
        
        if not password:
            errors['password'] = "Password is required"
        elif len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Z]', password):
            errors['password'] = "Password must be at least 8 characters, include a number and an uppercase letter"
        
        if not file:
            errors['image'] = "Image file is required"
        elif not allowed_file(file.filename):
            errors['image'] = "Invalid file format. Only allowed formats are JPG, PNG, and JPEG"
        
        if errors:
            return jsonify({"status": False, "errors": errors}), 422
        
        # Handle Image Upload
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure unique filename
            counter = 1
            while os.path.exists(file_path):
                filename = f"{counter}_{secure_filename(file.filename)}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                counter += 1
            file.save(file_path)
        
        # Hash password and create user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, dob=dob, place=place, address=address, image=filename, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Send welcome email to the user
        try:
            subject = f"Welcome to {blog_name}!"
            body = f"""
            Hello {name},
            
            Thank you for registering on our blog. We're excited to have you join our community!
            
            Best regards,
            The {blog_name} Team
            """
            
            msg = Message(subject, recipients=[email], bcc=[os.getenv('GMAIL_USER')])
            msg.body = body
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send welcome email: {str(e)}")

        return jsonify({
            "status": True,
            "message": "User registered successfully!",
            "User": {
                "id": new_user.id,
                "name": new_user.name,
                "dob": new_user.dob,
                "place": new_user.place,
                "address": new_user.address,
                "email": new_user.email,
                "image_url": new_user.image
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": False, "message": f"Registration failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validation Checks
        if not email:
            return jsonify({"status": False, "error": "Email is required"}), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"status": False, "error": "Invalid email format"}), 400
        
        if not password:
            return jsonify({"status": False, "error": "Password is required"}), 400
        elif len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Z]', password):
            return jsonify({"status": False, "error": "Password must be at least 8 characters, include a number and an uppercase letter"}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"status": False, "error": "Email not found"}), 404
        
        if not check_password_hash(user.password, password):
            return jsonify({"status": False, "error": "Incorrect password"}), 401

        # Generate JWT tokens
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "status": True,
            "message": "Login successful!",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }), 200

    except Exception as e:
        return jsonify({"status": False, "error": f"Login failed: {str(e)}"}), 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Forgot Password API - Sends a reset token to user email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        # Validate email
        if not email:
            return jsonify({"status": False, "error": "Email is required"}), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"status": False, "error": "Invalid email format"}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"status": False, "error": "Email not registered"}), 404

        # Generate a secure reset token and set expiration
        reset_token = secrets.token_hex(32)
        token_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Store token and expiry in the database
        user.reset_token = reset_token
        user.token_expiry = token_expiry
        db.session.commit()

        # Send Reset Email
        try:
            reset_link = f"{request.host_url}reset-password/{reset_token}"
            subject = "Password Reset Request"
            body = f"""
            Hello {user.name},

            We received a request to reset your password. Click the link below to reset it:
            
            {reset_link}

            This link will expire in 10 minutes.

            If you did not request this, please ignore this email.

            Regards,
            Your Team
            """
            msg = Message(subject, recipients=[email], body=body)
            mail.send(msg)
        except Exception as e:
            return jsonify({"status": False, "error": f"Failed to send email: {str(e)}"}), 500

        return jsonify({"status": True, "message": "Password reset email sent"}), 200

    except Exception as e:
        return jsonify({"status": False, "error": f"Forgot password failed: {str(e)}"}), 500


@app.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset Password API - Validates token and updates password"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        new_password = data.get('new_password', '')

        # Validate Inputs
        if not email:
            return jsonify({"status": False, "error": "Email is required"}), 400
        if not new_password:
            return jsonify({"status": False, "error": "New password is required"}), 400
        if len(new_password) < 8 or not re.search(r'\d', new_password) or not re.search(r'[A-Z]', new_password):
            return jsonify({"status": False, "error": "Password must be at least 8 characters long, include at least one number, one uppercase letter"}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"status": False, "error": "User not found"}), 404

        # Validate token
        if user.reset_token != token or user.token_expiry < datetime.now(timezone.utc):
            return jsonify({"status": False, "error": "Invalid or expired reset token"}), 400

        # Update password and clear reset token
        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.token_expiry = None
        db.session.commit()

        return jsonify({"status": True, "message": "Password reset successful!"}), 200

    except Exception as e:
        return jsonify({"status": False, "error": f"Reset password failed: {str(e)}"}), 500


@app.route("/post", methods=['GET'])
@jwt_required()
def post():
    posts = Posts.query.all()
    no_of_posts = 3
    page = int(request.args.get('page', 1))
    total_post = len(posts)
    last_page = math.ceil(total_post / no_of_posts)
    
    if page < 1:
        page = 1
    elif page > last_page:
        page = last_page
    
    start = (page - 1) * no_of_posts
    end = start + no_of_posts
    paginated_posts = posts[start:end]
    
    posts_data = [
        {
            "id": post.sno,
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "img_file": post.img_file,
            "date": post.date
        }
        for post in paginated_posts
    ]
    
    prev_page = f"/post?page={page - 1}" if page > 1 else None
    next_page = f"/post?page={page + 1}" if page < last_page else None
    
    response = [
        {
            "message": "Posts fetched successfully!",
            "current_page": page,
            "total_pages": last_page,
            "total_posts": total_post,
            "posts": posts_data,
            "prev_page": prev_page,   
            "next_page": next_page    
        }
    ]
    return make_response(jsonify(response), 200)

@app.route("/post/<string:post_slug>",methods = ['GET'])
@jwt_required()
def post_route(post_slug):
        post = Posts.query.filter_by(slug=post_slug).first()
        
        if not post:
            return make_response(jsonify({"error": "Post not found"}), 404)
        
        post_data = [
            {
                "id": post.sno,
                "title": post.title,
                "content": post.content,
                "slug": post.slug,
                "img_file": post.img_file,
                "date": post.date
            }
        ]
        
        return make_response(jsonify({"message": "Post fetched successfully!", "post": post_data}), 200)

@app.route("/edit/<string:sno>", methods=['GET', 'PUT'])
@jwt_required()
def edit_post(sno):
    if request.method == 'POST':
        data = request.get_json()
        box_title = data.get('title')
        box_slug = data.get('slug')
        box_content = data.get('content')
        box_img_file = data.get('img_file')
        date = datetime.now()

        if sno == '0':  # Creating a new post
            new_post = Posts(
                title=box_title,
                slug=box_slug,
                content=box_content,
                img_file=box_img_file,
                date=date
            )
            db.session.add(new_post)
            db.session.commit()
            return make_response(jsonify({"message": "New post added successfully"}), 201)

        else:  # Editing an existing post
            post = Posts.query.filter_by(sno=sno).first()
            if not post:
                return make_response(jsonify({"error": "Post not found"}), 404)

            post.title = box_title
            post.slug = box_slug
            post.content = box_content
            post.img_file = box_img_file
            post.date = date

            db.session.commit()
            return make_response(jsonify({"message": "Post updated successfully"}), 200)
    
    # Handle GET request to display existing post details for editing
    post = None if sno == '0' else Posts.query.filter_by(sno=sno).first()
    if not post:
        return make_response(jsonify({"error": "Post not found"}), 404)

    posts_data = [
            {
                "id": post.sno,
                "title": post.title,
                "content": post.content,
                "slug": post.slug, 
                "img_file": post.img_file, 
                "date": post.date
            }
            for post in [post]
        ]
    print(posts_data)
    return make_response(jsonify({"message": "Post GET successful!", "posts": posts_data}), 200)

@app.route("/contact", methods = ['POST'])
@jwt_required()
def contact():
        if(request.method=='POST'):
            '''Add entry to the database'''
            data = request.get_json()
            
            if not data:
                return make_response(jsonify({"error": "Invalid JSON data"}), 400)
            
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            message = data.get('message')
            
            if not name or not email or not phone or not message:
                return make_response(jsonify({"error": "Fields cannot be empty"}), 400)
            
            entry = Contacts(name=name,email=email,ph_no=phone,msg=message,date=datetime.now())
            db.session.add(entry)
            db.session.commit()
            return make_response(jsonify({
            "message": "Thanks for sending your details, we will get back to you soon",
            "contact": {
                "id": entry.sno,
                "name": entry.name,
                "email": entry.email,
                "phone": entry.ph_no,
                "message": entry.msg
            }
        }), 200)
        return make_response(jsonify({"message": "Failed to send details!"}), 401)

@app.route("/delete/<string:sno>",methods=['DELETE'])
@jwt_required()
def delete(sno):
        post = Posts.query.filter_by(sno=sno).first()
        if not post:
            return make_response(jsonify({"error": "Post not found"}), 404)
        db.session.delete(post)
        db.session.commit()
        return make_response(jsonify({"message": "Post deleted successfully!"}), 200)

@app.route("/search",methods = ['GET','POST'])
def search():
    data = request.get_json()
    # print(data)
    if request.method=='POST':
        query = data.get("search")
        # print(query)
        if not query:
            return make_response(jsonify({"error": "Search term cannot be empty"}), 400)
        results = Posts.query.filter(Posts.title.like(f"%{query}%")).all()
        if not results:
            return make_response(jsonify({"error": "No posts found"}), 404)
        posts_data = [
            {
                "id": post.sno,
                "title": post.title,
                "content": post.content,
                "slug": post.slug, 
                "img_file": post.img_file, 
                "date": post.date
            }
            for post in results
        ]
        return make_response(jsonify({"message": "Search successful!", "posts": posts_data}), 200)

@app.route("/uploader", methods=['POST'])
@jwt_required()
def uploader():
            f = request.files['file1']
            if f.filename == '':
                return make_response(jsonify({"error": "No file selected"}), 400)
            try:
                file = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], file))
                return make_response(jsonify({"success": "File uploaded successfully","File":file}), 201)
            except Exception as e:
                return make_response(jsonify({"error": f"An error occurred: {str(e)}"}), 500)

if __name__ == '__main__':
    app.run(debug=True)
