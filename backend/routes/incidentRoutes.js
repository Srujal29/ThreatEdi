const express = require('express');
const router = express.Router();
const incidentController = require('../controllers/incidentController');
const authenticateToken = require('../middleware/authMiddleware');
const { upload } = require('../config/cloudinary');

router.post('/', authenticateToken, upload.single('evidence'), incidentController.reportIncident);
router.post('/mitigation', authenticateToken, incidentController.generateMitigation);
router.get('/', authenticateToken, incidentController.getIncidents);
router.get('/:id', authenticateToken, incidentController.getIncidentById);
router.patch('/:id/status', authenticateToken, incidentController.updateIncidentStatus);

module.exports = router;
