const axios = require('axios');
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://127.0.0.1:8000/api';

exports.reportIncident = async (req, res) => {
    const { report_text, rank_id, unit_id } = req.body;
    
    // Map local uploads to accessible HTTP paths, otherwise use Cloudinary URL
    const evidence_url = req.file 
        ? (req.file.path.startsWith('http') ? req.file.path : `http://localhost:3000/uploads/${req.file.filename}`) 
        : null;

    if (!report_text) {
        return res.status(400).json({ error: 'report_text is required' });
    }

    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/incidents/report`, {
            user_id: req.user.user_id,
            report_text: report_text,
            evidence_url: evidence_url,
            rank_id: rank_id ? parseInt(rank_id) : null,
            unit_id: unit_id ? parseInt(unit_id) : null
        });

        res.json({
            message: 'Incident reported successfully',
            incident_data: pythonResponse.data
        });
    } catch (error) {
        console.error('Error calling Python microservice:', error.message);
        if (error.response) {
            return res.status(error.response.status).json({ error: error.response.data.detail || error.response.data.error || 'Failed to process incident' });
        }
        res.status(500).json({ error: 'Failed to process incident through ML pipeline' });
    }
};

exports.generateMitigation = async (req, res) => {
    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/ml/predict`, req.body);
        res.json(pythonResponse.data);
    } catch (error) {
        console.error('Error calling Python mitigation:', error.message);
        res.status(500).json({ error: 'Failed to generate mitigation' });
    }
};

exports.getIncidents = async (req, res) => {
    try {
        const { status, priority, limit } = req.query;
        const response = await axios.get(`${PYTHON_API_URL}/incidents/`, {
            params: { status, priority, limit }
        });
        res.json(response.data);
    } catch (error) {
        console.error('Error fetching incidents from Python microservice:', error.message);
        res.status(500).json({ error: 'Failed to fetch incidents' });
    }
};

exports.getIncidentById = async (req, res) => {
    try {
        const { id } = req.params;
        const response = await axios.get(`${PYTHON_API_URL}/incidents/${id}`);
        res.json(response.data);
    } catch (error) {
        if (error.response && error.response.status === 404) {
            return res.status(404).json({ error: 'Incident not found' });
        }
        console.error('Error fetching incident by ID from Python microservice:', error.message);
        res.status(500).json({ error: 'Failed to fetch incident details' });
    }
};

exports.updateIncidentStatus = async (req, res) => {
    try {
        const { id } = req.params;
        const { new_status } = req.body;

        if (!new_status) {
            return res.status(400).json({ error: 'new_status is required in body' });
        }

        const response = await axios.patch(`${PYTHON_API_URL}/incidents/${id}/status`, null, {
            params: { new_status }
        });
        res.json(response.data);
    } catch (error) {
        if (error.response) {
            return res.status(error.response.status).json({ error: error.response.data.detail || 'Failed to update status' });
        }
        console.error('Error updating incident status in Python microservice:', error.message);
        res.status(500).json({ error: 'Failed to update incident status' });
    }
};

