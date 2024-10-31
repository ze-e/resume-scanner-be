from flask import Flask, render_template, request, redirect, url_for
from resume_parser import screen_resume
from config_loader import load_job_criteria

app = Flask(__name__)

# Load job criteria once
job_criteria_list = load_job_criteria()['job_roles']

@app.route('/')
def index():
    return render_template('index.html', job_criteria_list=job_criteria_list)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    job_role_index = int(request.form['job_role'])

    if file and job_role_index < len(job_criteria_list):
        job_criteria = job_criteria_list[job_role_index]
        file_path = f"./uploads/{file.filename}"
        file.save(file_path)

        # Run the screening pipeline
        final_score = screen_resume(file_path, job_criteria)

        return render_template('result.html', score=final_score, job_role=job_criteria['role'])

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
