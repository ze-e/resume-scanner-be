import yaml

def load_job_criteria(file_path="job_criteria.yaml"):
    try:
        with open(file_path, "r") as file:
            job_criteria = yaml.safe_load(file)
            return job_criteria
    except Exception as e:
        print(f"Error loading job criteria: {e}")
        return None
