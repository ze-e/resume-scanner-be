import os
import yaml
import cloudinary
import requests
from io import StringIO

def load_job_criteria():
    data_source = os.getenv('DATA_SOURCE', 'local')  # Default to 'local' if not set

    try:
        if data_source == 'local':
            # Load from local YAML files
            all_roles = []
            local_directory = 'role_data'  
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
        print(f"Error loading job criteria: {e}")
        return {'job_roles': []}
