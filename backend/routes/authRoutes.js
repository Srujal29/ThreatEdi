const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const authenticateToken = require('../middleware/authMiddleware');

router.post('/login', authController.login);
router.post('/forgot-password', authController.forgotPassword);
router.post('/verify-otp', authController.verifyOtp);
router.post('/reset-password', authController.resetPassword);
router.post('/register', authController.register);
router.get('/ranks', authController.getRanks);
router.get('/units', authController.getUnits);
router.get('/users', authenticateToken, authController.getUsers);
router.get('/users/:id', authenticateToken, authController.getUserById);

module.exports = router;
