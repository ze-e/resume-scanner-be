import React, { useState, useEffect } from 'react';
import { Container, Typography, Button, Select, MenuItem, CircularProgress } from '@mui/material';

function App() {
    const [file, setFile] = useState(null);
    const [jobRole, setJobRole] = useState('');
    const [jobRoles, setJobRoles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const API_BASE_URL = (() => {
        const url = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';
        return url.split('#')[0].trim().replace(/\/$/, '');
    })();

    // Fetch job roles from the backend
    useEffect(() => {
        const fetchJobRoles = async () => {
            try {
                const url = new URL('/api/roles', API_BASE_URL).toString();
                console.log('Fetching from URL:', url);
                const response = await fetch(url);
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setJobRoles(data);
            } catch (error) {
                console.error('Detailed error:', error);
                console.error('Error stack:', error.stack);
                console.error('Error fetching job roles:', error);
                console.error('Current API_BASE_URL:', API_BASE_URL);
            }
        };

        fetchJobRoles();
    }, [API_BASE_URL]);

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleJobRoleChange = (event) => {
        setJobRole(event.target.value);
    };

    const handleSubmit = async () => {
        if (!file || !jobRole) {
            alert('Please select a file and job role');
            return;
        }
        setLoading(true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('job_role', jobRole);

        try {
            console.log('Submitting form data:', {
                file: file.name,
                jobRole: jobRole
            });
            
            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.text();
                console.error('Server response:', errorData);
                throw new Error(`Server error: ${errorData}`);
            }

            const data = await response.json();
            setResult(data); 
        } catch (error) {
            console.error('Detailed error:', error);
            alert(`Error uploading resume: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm" style={{ marginTop: '50px' }}>
            <Typography variant="h4" gutterBottom>
                Resume Screener
            </Typography>

            <input
                accept=".pdf,.docx"
                style={{ display: 'none' }}
                id="raised-button-file"
                type="file"
                onChange={handleFileChange}
            />
            <label htmlFor="raised-button-file">
                <Button variant="contained" component="span">
                    Upload Resume
                </Button>
            </label>
            {file && <Typography variant="body1">{file.name}</Typography>}

            <Select
                value={jobRole}
                onChange={handleJobRoleChange}
                displayEmpty
                fullWidth
                style={{ marginTop: '20px' }}
            >
                <MenuItem value="" disabled>
                    Select Job Role
                </MenuItem>
                {jobRoles.map((role, index) => (
                    <MenuItem key={index} value={role}>
                        {role}
                    </MenuItem>
                ))}
            </Select>

            <Button
                variant="contained"
                color="primary"
                onClick={handleSubmit}
                style={{ marginTop: '20px' }}
            >
                Submit
            </Button>

            {loading && (
                <div style={{ marginTop: '20px' }}>
                    <CircularProgress />
                    <Typography variant="body1">Processing resume...</Typography>
                </div>
            )}

            {result && (
                <div style={{ marginTop: '20px' }}>
                    <Typography variant="h6">Results:</Typography>
                    <Typography variant="body1">Score without ChatGPT: {result.score_without_chatgpt}</Typography>
                    <Typography variant="body1">Score with ChatGPT: {result.score_with_chatgpt}</Typography>
                    <Typography variant="body1">ChatGPT Summary: {result.summary}</Typography>
                </div>
            )}
        </Container>
    );
}

export default App;
