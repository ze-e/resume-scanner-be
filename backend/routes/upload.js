const cloudinary = require('../config/cloudinary');

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const result = await cloudinary.uploader.upload(req.file.path, {
      resource_type: 'auto' // automatically detect file type
    });
    
    // Store the Cloudinary URL instead of local file path
    const fileUrl = result.secure_url;
    
    // Update your database with fileUrl instead of local path
    
    res.json({ url: fileUrl });
  } catch (error) {
    res.status(500).json({ error: 'Upload failed' });
  }
}); 