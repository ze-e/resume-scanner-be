import yaml
import os

def load_job_criteria():
    try:
        role_data_dir = 'role_data'
        combined_data = {'job_roles': []}
        
        # List all YAML files in the role_data directory
        yaml_files = [f for f in os.listdir(role_data_dir) if f.endswith('.yaml') or f.endswith('.yml')]
        
        # Load each YAML file and combine the data
        for yaml_file in yaml_files:
            file_path = os.path.join(role_data_dir, yaml_file)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data and isinstance(data, dict):
                    # Assuming each YAML file contains a single job role
                    combined_data['job_roles'].append(data)
        
        print(f"Loaded job criteria: {combined_data}")
        return combined_data
    except Exception as e:
        print(f"Error loading job criteria: {str(e)}")
        return None
