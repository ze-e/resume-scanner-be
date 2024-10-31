from flask import Flask, request, jsonify, render_template
from resume_parser import screen_resume
from config_loader import load_job_criteria
from flask_cors import CORS
import os
import yaml
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Load job criteria once
try:
    job_criteria_list = load_job_criteria()['job_roles']
except (TypeError, KeyError):
    print("Warning: Failed to load job criteria. Using empty list as fallback.")
    job_criteria_list = []

@app.route('/')
def index():
    return render_template('index.html', job_criteria_list=job_criteria_list)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        print("Files received:", request.files)
        print("Form data received:", request.form)
        
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

        # Delete the temporary file
        os.remove(file_path)

        return jsonify(final_score)

    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    try:
        print("Fetching job roles...")
        criteria = load_job_criteria()
        if not criteria or 'job_roles' not in criteria:
            return jsonify([]), 200
            
        # Extract just the role names from each job role object
        roles = [role.get('role') for role in criteria['job_roles'] if role.get('role')]
        print(f"Found roles: {roles}")
        return jsonify(roles)
    except Exception as e:
        print(f"Error fetching roles: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
