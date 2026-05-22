const axios = require('axios');
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://127.0.0.1:8000/api';

exports.reportIncident = async (req, res) => {
    const { report_text } = req.body;
    const evidence_url = req.file ? req.file.path : null;

    if (!report_text) {
        return res.status(400).json({ error: 'report_text is required' });
    }

    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/incidents/report`, {
            user_id: req.user.user_id,
            report_text: report_text,
            evidence_url: evidence_url
        });

        res.json({
            message: 'Incident reported successfully',
            incident_data: pythonResponse.data
        });
    } catch (error) {
        console.error('Error calling Python microservice:', error.message);
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
