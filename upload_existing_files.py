import os
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

def upload_existing_files():
    # Path to your local role_data directory
    role_data_dir = 'role_data'
    
    for filename in os.listdir(role_data_dir):
        if filename.endswith('.yaml'):
            file_path = os.path.join(role_data_dir, filename)
            
            # Upload file to Cloudinary
            try:
                result = cloudinary.uploader.upload(
                    file_path,
                    resource_type="raw",
                    public_id=f"role_data/{filename}",
                    folder="role_data",
                    format="yaml"
                )
                print(f"Uploaded {filename}: {result['secure_url']}")
            except Exception as e:
                print(f"Error uploading {filename}: {e}")

if __name__ == "__main__":
    upload_existing_files() 