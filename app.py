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
from io import BytesIO, StringIO  
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
allowed_origins = os.getenv('ALLOWED_ORIGINS', '')
# allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
logger.info(allowed_origins)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": allowed_origins}})  
# CORS(app)  
# Add Cloudinary configuration after Flask initialization
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

# Load job criteria based on the data source
def load_job_criteria():
    data_source = os.getenv('DATA_SOURCE', 'local')  # Default to 'local' if not set

    try:
        if data_source == 'local':
            # Load from local YAML files
            all_roles = []
            local_directory = 'role_data'  # Adjust this path as necessary
            for filename in os.listdir(local_directory):
                if filename.endswith('.yaml'):
                    with open(os.path.join(local_directory, filename), 'r') as file:
                        yaml_content = yaml.safe_load(file)
                        all_roles.append(yaml_content)
            return {'job_roles': all_roles}

        elif data_source == 'cloudinary':
            # Load from Cloudinary
            result = cloudinary.api.resources(
                resource_type="raw",
                prefix="role_data/",
                type="upload"
            )

            all_roles = []
            for resource in result['resources']:
                # Download each YAML file
                response = requests.get(resource['secure_url'])
                if response.status_code == 200:
                    # Parse YAML content
                    yaml_content = yaml.safe_load(StringIO(response.text))
                    all_roles.append(yaml_content)

            return {'job_roles': all_roles}

        else:
            raise ValueError("Invalid data source specified. Use 'local' or 'cloudinary'.")

    except Exception as e:
        logger.error(f"Error loading job criteria: {e}")
        return {'job_roles': []}

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
        
        # Upload to Cloudinary or save locally based on data source
        data_source = os.getenv('DATA_SOURCE', 'local')
        if data_source == 'cloudinary':
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                BytesIO(yaml_content.encode()),
                resource_type="raw",
                public_id=f"role_data/{filename}",
                folder="role_data",
                format="yaml"
            )
            logger.info("Role file uploaded to Cloudinary: %s", upload_result['secure_url'])
            url = upload_result['secure_url']
        else:
            # Save locally
            local_directory = 'role_data'  # Adjust this path as necessary
            os.makedirs(local_directory, exist_ok=True)
            with open(os.path.join(local_directory, filename), 'w') as file:
                file.write(yaml_content)
            logger.info("Role file saved locally: %s", filename)
            url = f"file://{os.path.abspath(os.path.join(local_directory, filename))}"

        # Reload job criteria
        global job_criteria_list
        job_criteria_list = load_job_criteria()['job_roles']

        return jsonify({'message': 'Role created successfully', 'url': url}), 201

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
