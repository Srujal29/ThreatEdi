const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const transporter = require('../config/email');

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://127.0.0.1:8000/api';

exports.login = async (req, res) => {
    const { email, password } = req.body;
    try {
        const response = await axios.get(`${PYTHON_API_URL}/internal/users/email/${email}`);
        const user = response.data;
        
        const isMatch = await bcrypt.compare(password, user.password_hash);
        if (!isMatch) {
            return res.status(401).json({ error: 'Invalid password' });
        }

        const token = jwt.sign({ user_id: user.user_id, email: user.email, rank_id: user.rank_id, unit_id: user.unit_id }, process.env.JWT_SECRET || 'fallback_secret', { expiresIn: '8h' });
        res.json({ token, user: { id: user.user_id, email: user.email, name: user.full_name, service_number: user.service_number } });
    } catch (err) {
        if (err.response && err.response.status === 404) {
            return res.status(404).json({ error: 'User not found' });
        }
        res.status(500).json({ error: err.message });
    }
};

exports.forgotPassword = async (req, res) => {
    const { email } = req.body;
    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/internal/otps`, { email });
        const otp = pythonResponse.data.otp_code;

        const mailOptions = {
            from: `"ThreatEdi" <yashwadhwani7867@gmail.com>`,
            to: email,
            subject: 'Password Reset OTP',
            text: `Your password reset OTP is: ${otp}\n\nIt expires in 15 minutes.`,
            html: `<h3>Password Reset</h3><p>Your password reset OTP is: <strong>${otp}</strong></p><p>It expires in 15 minutes.</p>`
        };

        transporter.sendMail(mailOptions, (error, info) => {
            if (error) {
                return res.status(500).json({ error: error.message });
            }
            res.json({ message: 'If the email exists, an OTP was sent.' });
        });
    } catch (err) {
        if (err.response && err.response.status === 404) {
            return res.status(200).json({ message: 'If the email exists, an OTP was sent.' });
        }
        res.status(500).json({ error: err.message });
    }
};

exports.verifyOtp = async (req, res) => {
    const { email, otp_code } = req.body;
    try {
        await axios.post(`${PYTHON_API_URL}/internal/otps/verify`, { email, otp_code });
        res.json({ message: 'OTP verified successfully' });
    } catch (err) {
        if (err.response && err.response.status === 400) {
            return res.status(400).json({ error: err.response.data.detail });
        }
        res.status(500).json({ error: 'Failed to verify OTP' });
    }
};

exports.resetPassword = async (req, res) => {
    const { email, otp_code, new_password } = req.body;
    try {
        await axios.post(`${PYTHON_API_URL}/internal/otps/verify`, { email, otp_code });
        
        const salt = await bcrypt.genSalt(10);
        const new_password_hash = await bcrypt.hash(new_password, salt);

        await axios.patch(`${PYTHON_API_URL}/internal/users/password`, { email, new_password_hash });

        res.json({ message: 'Password updated successfully' });
    } catch (err) {
        if (err.response && err.response.status === 400) {
            return res.status(400).json({ error: err.response.data.detail });
        }
        res.status(500).json({ error: 'Failed to reset password' });
    }
};
