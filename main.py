import os
import math
import re
import secrets
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity,unset_jwt_cookies
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from flask_cors import CORS
from flask_migrate import Migrate
from faker import Faker
from slugify import slugify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from models import Contacts,User,Posts,db

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
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
fake = Faker()

# File upload configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('GMAIL_USER')
mail = Mail(app)

# Blog Configurations
blog_name = os.getenv('BLOG_NAME')
about_txt = os.getenv('ABOUT_TXT')
no_of_posts = int(os.getenv('NO_OF_POSTS'))

# Social Media URLs
fb_url = os.getenv('FB_URL')
x_url = os.getenv('X_URL')
git_url = os.getenv('GIT_URL')

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
            Your Team Code Hunter
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
    try:
        data = request.get_json()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')

        errors = {}

        if not new_password:
            return jsonify({"status": False, "error": "Password is required"}), 400
        elif len(new_password) < 8 or not re.search(r'\d', new_password) or not re.search(r'[A-Z]', new_password):
            return jsonify({"status": False, "error": "Password must be at least 8 characters, include a number and an uppercase letter"}), 400
        if not confirm_password:
            errors["confirm_password"] = "Confirm password is required."
        elif confirm_password != new_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            return jsonify({"status": False, "errors": errors}), 400

        # Find user by token
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return jsonify({"status": False, "error": "Invalid or expired reset token"}), 400

        # Validate token expiry (fixing the timezone issue)
        if user.token_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return jsonify({"status": False, "error": "Token has expired"}), 400

        # Update password and clear reset token
        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.token_expiry = None
        db.session.commit()

        # Send email notification
        try:
            subject = "Password Reset Successful!"
            body = f"""
            Hello {user.name},

            Your password has been successfully reset. If you did not request this change, please contact support immediately.

            Best Regards,  
            The Team Code Hunter
            """
            msg = Message(subject, recipients=[user.email],body=body)
            msg.body = body
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send reset password email: {str(e)}")

        return jsonify({"status": True, "message": "Password reset successful! A confirmation email has been sent."}), 200

    except Exception as e:
        return jsonify({"status": False, "error": f"Reset password failed: {str(e)}"}), 500

@app.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()

        errors = {}

        if not current_password:
            errors["current_password"] = "Current password is required."

        if not new_password:
            return jsonify({"status": False, "error": " New Password is required"}), 400
        elif len(new_password) < 8 or not re.search(r'\d', new_password) or not re.search(r'[A-Z]', new_password):
            return jsonify({"status": False, "error": " New Password must be at least 8 characters, include a number and an uppercase letter"}), 400

        if not confirm_password:
            errors["confirm_password"] = "Confirm password is required."
        elif confirm_password != new_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            return jsonify({"status": False, "errors": errors}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": False, "error": "User not found"}), 404

        if not check_password_hash(user.password, current_password):
            return jsonify({"status": False, "error": "Incorrect current password"}), 401

        if check_password_hash(user.password, new_password):
            return jsonify({"status": False, "error": "New password cannot be the same as the old password"}), 400

        user.password = generate_password_hash(new_password)
        db.session.commit()

        # Force logout by unsetting all JWT cookies
        response = jsonify({"status": True, "message": "Password changed successfully! You have been logged out on all devices."})
        unset_jwt_cookies(response)

        # Send email notification
        try:
            subject = "Password Change Notification"
            body = f"""
            Hello {user.name},

            Your password has been successfully changed. If you did not request this change, please contact support immediately.

            Best Regards,  
            The Team Code Hunter
            """
            msg = Message(subject, recipients=[user.email])
            msg.body = body
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send password change email: {str(e)}")

        return response

    except Exception as e:
        return jsonify({"status": False, "error": f"Password change failed: {str(e)}"}), 500

@app.route('/random_post/<int:user_id>', methods=['POST'])
def random_post(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": False, "error": "User not found!"}), 404
    
    for _ in range(5):  # Generate exactly 5 posts
        title = fake.sentence()
        base_slug = slugify(title)
        
        # Ensure unique slug
        unique_slug = base_slug
        count = 1
        while Posts.query.filter_by(slug=unique_slug).first():
            unique_slug = f"{base_slug}-{count}"
            count += 1
        
        post = Posts(
            user_id=user_id,
            title=title,
            slug=unique_slug,
            content=fake.text(),
            date=datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            img_file=f"https://picsum.photos/200/300?random={random.randint(1, 100)}"
        )
        db.session.add(post)
    db.session.commit()  # Commit all 5 posts in a single transaction

    return jsonify({
        "status": True,
        "message": f"5 random posts created successfully for user {user_id}!"
    }), 201

@app.route("/post", methods=['GET'])
def get_posts():
    try:
        # Get query parameters from the request URL
        search_query = request.args.get("search", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 2, type=int)

        if search_query:
            posts_query = posts_query.filter(Posts.title.ilike(f"%{search_query}%"))

        posts_paginated = Posts.query.paginate(page=page, per_page=per_page, error_out=False)

        if not posts_paginated.items:
            return jsonify({"error": "No posts found", "status": False}), 404

        posts_data = [
            {
                "id": post.sno,
                "title": post.title,
                "content": post.content,
                "slug": post.slug,
                "img_file": post.img_file,
                "date": post.date if post.date else None
            }
            for post in posts_paginated.items
        ]

        return jsonify({
            "message": "Posts fetched successfully!",
            "status": True,
            "search_query": search_query,
            "current_page": page,
            "per_page": per_page,
            "total_pages": posts_paginated.pages,
            "total_posts": posts_paginated.total,
            "posts": posts_data
        }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}", "status": False}), 500

@app.route("/post/<string:post_slug>",methods = ['GET'])
def post_slug(post_slug):
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
                "date": post.date,
                "user_id": post.user_id
            }
        ]
        return make_response(jsonify({"message": "Post fetched successfully!","status": True, "post": post_data}), 200)

@app.route("/add",methods=['POST'])
@jwt_required()
def add_post():
    try:
        user_id = get_jwt_identity()
        data = request.form
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        img_file = request.files.get('img_file')
        date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        if not title:
            return jsonify({"error": "Title is required!","status": False}), 400
        if len(title) < 3 or len(title) > 100:
            return jsonify({"error": "Title must be between 3 and 100 characters!","status": False}), 400

        if not content:
            return jsonify({"error": "Content is required!"}), 400
        if len(content) < 10 or len(content) > 5000:
            return jsonify({"error": "Content must be between 10 and 5000 characters!","status": False}), 400
        
        if not img_file:
            return jsonify({"error": "Image file is required!","status": False}), 400
    
        # Generate Unique Slug from Title
        base_slug = slugify(title)
        unique_slug = base_slug
        count = 1
        while Posts.query.filter_by(slug=unique_slug).first():
            unique_slug = f"{base_slug}-{count}"
            count += 1
        
        # Image Upload
        filename = None
        if img_file and img_file.filename:
            if not allowed_file(img_file.filename):
                return jsonify({"error": "Invalid file type! Only JPG, JPEG, PNG allowed.","status": False}), 400

            filename = secure_filename(img_file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                img_file.save(upload_path)
            except Exception as e:
                return jsonify({"error": "Failed to upload image!", "details": str(e)}), 500

        new_post = Posts(
            title=title, slug=unique_slug, content=content,
            date=date, img_file=filename, user_id=user_id
        )
        db.session.add(new_post)
        db.session.commit()

        return jsonify({
            "message": "Post added successfully!",
            "status": True,
            "post": {
                "id": new_post.sno,
                "title": new_post.title,
                "slug": new_post.slug,
                "content": new_post.content,
                "date": new_post.date,
                "img_file": new_post.img_file,
                "user_id": new_post.user_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong!", "details": str(e)}), 500

@app.route("/edit/<int:sno>", methods=['GET','PUT'])
@jwt_required()
def edit_post(sno):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Unauthorized! Please log in.","status": False}), 401
        
        post = Posts.query.get(sno)
        if not post:
            return jsonify({"error": f"Post with ID {sno} not found!","status": False}), 404

        if post.user_id != user.id:
            return jsonify({"error": "You are not authorized to edit this post!","status": False}), 403
        
        if request.method == 'GET':
            return jsonify({
                "post": {
                    "id": post.sno,
                    "title": post.title,
                    "slug": post.slug,
                    "content": post.content,
                    "date": post.date,
                    "img_file": post.img_file,
                    "user_id": post.user_id
                }
            }), 200
        
        if request.method == 'PUT':
            data = request.form
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            img_file = request.files.get('img_file')

            if not title:
                return jsonify({"error": "Title is required!","status": False}), 400
            if len(title) < 3 or len(title) > 100:
                return jsonify({"error": "Title must be between 3 and 100 characters!","status": False}), 400

            if not content:
                return jsonify({"error": "Content is required!","status": False}), 400
            if len(content) < 10 or len(content) > 5000:
                return jsonify({"error": "Content must be between 10 and 5000 characters!","status": False}), 400

            base_slug = slugify(title)
            unique_slug = base_slug
            count = 1
            while Posts.query.filter(Posts.slug == unique_slug, Posts.sno != sno).first():
                unique_slug = f"{base_slug}-{count}"
                count += 1

            # Update post fields
            post.title = title
            post.slug = unique_slug
            post.content = content
            post.date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

            if img_file and allowed_file(img_file.filename):
                filename = secure_filename(img_file.filename)
                img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.img_file = filename

            db.session.commit()

            return jsonify({
                "message": "Post updated successfully!",
                "status": True,
                "post": {
                    "id": post.sno,
                    "title": post.title,
                    "slug": post.slug,
                    "content": post.content,
                    "date": post.date,
                    "img_file": post.img_file,
                    "user_id": post.user_id
                }
            }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong!", "details": str(e)}), 500

@app.route("/delete/<int:sno>", methods=['DELETE'])
@jwt_required()
def delete_post(sno):
    user_id = int(get_jwt_identity())
    
    post = Posts.query.get(sno)
    if not post:
        return jsonify({"error": "Post not found!","status": False}), 404
    if post.user_id != user_id:
        return jsonify({
                "error": "Unauthorized! You can only delete your own posts.",
                "status": False,
                "expected_user": post.user_id,
                "provided_user": user_id
            }), 403
    
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({
            "message": "Post deleted successfully!",
            "status": True,
            "deleted_post": {
                "id": post.sno,
                "title": post.title,
                "slug": post.slug,
                "deleted_at": datetime.now().strftime("%d-%m-%Y %I:%M %p")
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while deleting the post.", "details": str(e)}), 500

@app.route("/contact", methods = ['POST'])
def contact():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()
    date = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    
    # Validation errors
    errors = {}

    if not name:
            errors['name'] = "Name is required"
    elif not re.match(r"^[A-Za-z\s]+$", name):
            errors['name'] = "Name must contain only letters and spaces"

    if not email:
            errors['email'] = "Email is required"
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors['email'] = "Invalid email format"

    if not phone:
        errors['phone'] = "Phone number is required"
    elif not re.match(r'^\d{10}$', phone):
        errors['phone'] = "Phone number must be exactly 10 digits long"

    if not message:
        errors['message'] = "Message is required"
    elif len(message) < 10:
        errors['message'] = "Message must be at least 10 characters long"

    if errors:
        return jsonify({"status": False, "errors": errors}), 400

    try:
        new_contact = Contacts(name=name, email=email, ph_no=phone, msg=message, date=date)
        db.session.add(new_contact)
        db.session.commit()

        # Send email to admin
        admin_email = app.config.get('MAIL_USERNAME')
        subject = f"New Contact Form Submission from {name}"
        body = f"""
        Name: {name}
        Email: {email}
        Phone: {phone}
        Message: {message}
        Date: {date}
        """

        msg = Message(subject, sender=email, recipients=[admin_email])
        msg.body = body
        mail.send(msg)

        return jsonify({"status": True, "message": "Your message has been sent successfully!"}), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Contact form submission error: {str(e)}")
        return jsonify({"status": False, "error": "Something went wrong! Please try again later.", "details": str(e)}), 500

@app.route("/user/posts", methods=['GET'])
@jwt_required()
def user_posts():
    try:
        current_user_id = get_jwt_identity()
        
        per_page = request.args.get("per_page", default=2, type=int)
        page = max(1, request.args.get("page", 1, type=int))
        search_query = request.args.get("search", default="", type=str).strip()

        posts_query = Posts.query.filter_by(user_id=current_user_id)
        
        if search_query:
            posts_query = posts_query.filter(Posts.title.ilike(f"%{search_query}%"))
        
        posts_paginated = posts_query.paginate(page=page, per_page=per_page, error_out=False)

        # If no posts found
        if not posts_paginated.items:
            return jsonify({"error": "No posts found", "status": False}), 404

        posts_data = [
            {
                "id": post.sno,
                "title": post.title,
                "content": post.content,
                "slug": post.slug,
                "img_file": post.img_file,
                "date": post.date
            }
            for post in posts_paginated.items
        ]
        
        return jsonify({
            "status": True,
            "message": "User posts fetched successfully!",
            "current_page": page,
            "per_page": per_page,
            "total_pages": posts_paginated.pages or 1,
            "total_posts": posts_paginated.total,
            "posts": posts_data
        }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}", "status": False}), 500

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    try:
        # Get the user ID from JWT token
        user_id = int(get_jwt_identity())

        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": False, "error": "User not found"}), 404

        return jsonify({
            "status": True,
            "message": "User profile fetched successfully!",
            "user": {
                "id": user.id,
                "name": user.name,
                "dob": user.dob,
                "place": user.place,
                "address": user.address,
                "email": user.email,
                "image_url": user.image
            }
        }), 200

    except Exception as e:
        return jsonify({"status": False, "error": f"Error fetching profile: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
