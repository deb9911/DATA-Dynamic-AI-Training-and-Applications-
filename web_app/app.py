import os
from flask import Flask, render_template, request, logging, jsonify, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from urllib.parse import quote
import jwt
import requests
from werkzeug.utils import secure_filename
from elasticsearch import Elasticsearch
import pdfplumber
from docx import Document


# from es_dev import create_ES_index


app = Flask(__name__, template_folder='templates')
UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'Shivaa@2025'
TENANT_ID = "<YOUR_TENANT_ID>"
# JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
# Configure Elasticsearch client
app.config['ELASTICSEARCH_HOST'] = 'http://localhost:9200'  # Update with your Elasticsearch URL
es = Elasticsearch(app.config['ELASTICSEARCH_HOST'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

users = {"admin": generate_password_hash("password123")}

# Test Elasticsearch connection
if es.ping():
    print("Connected to Elasticsearch!")
else:
    print("Failed to connect to Elasticsearch.")


def create_ES_index(es):
    index_name = "datasets"

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "settings": {
                "number_of_shards": 1,  # ✅ Reduce shards for single-node setup
                "number_of_replicas": 0  # ✅ No replicas for single-node
            },
            "mappings": {
                "properties": {
                    "file_name": {"type": "text"},
                    "upload_time": {"type": "date"},
                    "content": {"type": "text"}
                }
            }
        })
        print(f"Index '{index_name}' created!")
    return index_name


# index_name = create_ES_index(es)


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            user = User(username)
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


# def verify_token(token):
#     jwks = requests.get(JWKS_URL).json()
#     header = jwt.get_unverified_header(token)
#     key = next(k for k in jwks['keys'] if k['kid'] == header['kid'])
#     return jwt.decode(token, key, algorithms=['RS256'], audience="<YOUR_CLIENT_ID>")


# @app.route('/api/protected')
# def protected():
#     token = request.headers.get('Authorization').split(" ")[1]
#     try:
#         claims = verify_token(token)
#         return jsonify({"message": "Access granted", "claims": claims})
#     except Exception as e:
#         return jsonify({"error": "Invalid token"}), 401


@app.route('/')
@login_required
def index():
    return render_template('base.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route('/file-operation')
@login_required
def file_operation():
    return render_template("File_ops.html")


@app.route('/es')
@login_required
def es_page():
    return render_template('es.html')


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Process the dataset (example: load and preview using pandas)
    try:
        if file.filename.endswith('.csv'):
            # Handle CSV files
            df = pd.read_csv(file_path)
        elif file.filename.endswith('.xlsx'):
            # Handle Excel files with .xlsx extension
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file.filename.endswith('.xls'):
            # Handle Excel files with .xls extension
            df = pd.read_excel(file_path, engine='xlrd')
        else:
            return jsonify({'error': 'Unsupported file format. Please upload .csv, .xls, or .xlsx files.'}), 400

        # Generate HTML for the table
        table_html = quote(df.to_html(classes='table table-striped table-bordered'))
        return jsonify({'table': table_html, 'filename': file.filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


def extract_text(file_path, file_ext):
    """Extracts text content from different file formats"""
    content = ""

    if file_ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

    if file_ext == ".csv":
        df = pd.read_csv(file_path)
        # Convert DataFrame to a string including column names
        content = " ".join(df.columns) + "\n" + df.to_string(index=False)

    elif file_ext == ".xlsx" or file_ext == ".xls":
        df = pd.read_excel(file_path, engine="openpyxl")
        content = " ".join(df.columns) + "\n" + df.to_string(index=False)

    elif file_ext == ".docx":
        doc = Document(file_path)
        content = "\n".join([p.text for p in doc.paragraphs])

    elif file_ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    return content


@app.route("/upload-to-es", methods=["POST"])
def upload_to_es():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in [".txt", ".csv", ".docx", ".pdf"]:
        return jsonify({"error": "Unsupported file format"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Extract text content
    content = extract_text(file_path, file_ext)

    if not content.strip():
        return jsonify({"error": "No extractable content in file"}), 400

    # Index document in Elasticsearch
    document = {
        "file_name": filename,
        "file_type": file_ext,
        "upload_time": "2025-01-29T12:00:00",  # Replace with dynamic timestamp
        "content": content
    }
    index_name = create_ES_index(es)
    # res = es.index(index="documents_index", body=document, id=None)
    res = es.index(index=index_name, body=document, id=None)

    return jsonify({"message": "File indexed successfully", "id": res["_id"]})


@app.route("/uploaded-docs", methods=["GET"])
@login_required
def uploaded_docs():
    files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"])]
    return jsonify(files)


@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'match')  # Default is 'match'

    if not query:
        return jsonify([])

    index_name = "datasets"

    # Choose Query Type
    if search_type == "match":
        query_body = {"query": {"match": {"content": query}}}
    elif search_type == "match_all":
        query_body = {"query": {"match_all": {}}}
    elif search_type == "wildcard":
        query_body = {"query": {"wildcard": {"content": f"*{query}*"}}}
    else:
        return jsonify({"error": "Invalid search type"}), 400

    response = es.search(index=index_name, body=query_body)

    seen = set()
    results = []
    for hit in response["hits"]["hits"]:
        file_name = hit["_source"]["file_name"]
        if file_name not in seen:
            seen.add(file_name)
            results.append({"file_name": file_name})

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)

