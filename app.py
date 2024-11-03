from flask import Flask, request, jsonify
from resume_parser import screen_resume
from config_loader import load_job_criteria
from flask_cors import CORS
import os
import yaml
import logging
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from io import BytesIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Add Cloudinary configuration after Flask initialization
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

# Load job criteria once
try:
    job_criteria_list = load_job_criteria()['job_roles']
    logger.info("Successfully loaded job criteria")
except (TypeError, KeyError) as e:
    logger.warning(f"Failed to load job criteria. Using empty list as fallback. Error: {str(e)}")
    job_criteria_list = []

@app.route('/')
def index():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy", "message": "Resume Scanner API is running"}), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("Files received: %s", request.files)
        logger.info("Form data received: %s", request.form)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        job_role = request.form.get('job_role')
        if not job_role:
            return jsonify({'error': 'No job role specified'}), 400

        # Create uploads directory if it doesn't exist
        os.makedirs('./uploads', exist_ok=True)

        # Save the file temporarily
        file_path = os.path.join('./uploads', secure_filename(file.filename))
        file.save(file_path)
        logger.info("File saved temporarily at: %s", file_path)

        # Load job criteria and find matching role
        criteria = load_job_criteria()
        if not criteria or 'job_roles' not in criteria:
            return jsonify({'error': 'Job criteria not found'}), 400

        job_criteria = next(
            (role for role in criteria['job_roles'] if role['role'] == job_role),
            None
        )

        if not job_criteria:
            return jsonify({"error": f"Invalid job role: {job_role}"}), 400

        # Process the resume
        final_score = screen_resume(file_path, job_criteria)
        logger.info("Resume processed successfully for role: %s", job_role)

        # Delete the temporary file
        os.remove(file_path)

        return jsonify(final_score)

    except Exception as e:
        logger.error("Error processing upload: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    try:
        logger.info("Fetching job roles...")
        criteria = load_job_criteria()
        if not criteria or 'job_roles' not in criteria:
            return jsonify([]), 200
            
        roles = [role.get('role') for role in criteria['job_roles'] if role.get('role')]
        logger.info("Found roles: %s", roles)
        return jsonify(roles)
    except Exception as e:
        logger.error("Error fetching roles: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/roles', methods=['POST'])
def create_role():
    try:
        role_data = request.json
        logger.info("Received new role data: %s", role_data)
        
        # Validate required fields
        required_fields = ['role', 'skills', 'experience_keywords', 'education', 'weights']
        if not all(field in role_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Create filename from role name
        filename = f"{role_data['role'].lower().replace(' ', '_')}.yaml"
        
        # Convert role_data to YAML string
        yaml_content = yaml.dump(role_data, allow_unicode=True)
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            BytesIO(yaml_content.encode()),
            resource_type="raw",
            public_id=f"role_data/{filename}",
            folder="role_data",
            format="yaml"
        )
        
        logger.info("Role file uploaded to Cloudinary: %s", upload_result['secure_url'])

        # Reload job criteria
        global job_criteria_list
        job_criteria_list = load_job_criteria()['job_roles']

        return jsonify({'message': 'Role created successfully', 'url': upload_result['secure_url']}), 201

    except Exception as e:
        logger.error("Error creating role: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_error(error):
    logger.error("An error occurred: %s", str(error), exc_info=True)
    return jsonify({"error": str(error)}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info("Starting application on port %s", port)
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        logger.error("Failed to start application: %s", str(e), exc_info=True)
        raise
