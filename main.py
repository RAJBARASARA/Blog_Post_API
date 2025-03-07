from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail, Message
import json, math, os, re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.secret_key)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Token expires after 1 hour

# Database Configuration
local_server = os.getenv('LOCAL_SERVER', 'True').lower() == 'true'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('LOCAL_URL') if local_server else os.getenv('PROD_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# File upload configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', "static/assets/img")
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

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"message": "Invalid name, email, or password"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400

    new_user = User(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User Registered successfully!"}), 201

@app.route('/login',methods=['POST'])
def login():
    if request.method=='POST':
        data = request.get_json() 
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.password==password:
            access_token = create_access_token(identity=str(user.id))
            return jsonify({"message": "Login successful!", "access_token": access_token}), 200
        return jsonify({"message": "Invalid credentials"}), 401

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

upload_folder = "C:\\Users\\rajup\\Desktop\\R\\Python Training\\5.Framework\\Blog-post Api\\static\\assets\\file"
app.config['UPLOAD_FOLDER'] = upload_folder

if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

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

app.run(debug=True)