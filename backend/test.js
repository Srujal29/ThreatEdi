const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

const NODE_API = 'http://localhost:3000/api';

async function runTests() {
    console.log('--- SEEDING yashwadhwani7867@gmail.com ---');
    try {
        await axios.post('http://127.0.0.1:8000/api/internal/users', {
            user_id: 'test-user-yash',
            full_name: 'Yash Wadhwani',
            email: 'yashwadhwani7867@gmail.com',
            service_number: 'SN-999',
            password_hash: '$2a$10$xyz', // Dummy hash
            user_type: 'Active',
            rank_id: 8,
            unit_id: 1
        });
        console.log('Seeded Yash.');
    } catch(e) { console.log('Already seeded or error:', e.message); }

    console.log('\n--- 1. TESTING LOGIN ---');
    let token = '';
    try {
        const res = await axios.post(`${NODE_API}/auth/login`, { email: 'john.doe@army.mil', password: 'password123' });
        console.log('Login Success! Token received:', res.data.token.substring(0, 20) + '...');
        token = res.data.token;
    } catch (e) {
        console.log('Login failed:', e.response?.data || e.message);
    }

    console.log('\n--- 2. TESTING FORGOT PASSWORD ---');
    try {
        const res = await axios.post(`${NODE_API}/auth/forgot-password`, { email: 'yashwadhwani7867@gmail.com' });
        console.log('Forgot Password response:', res.data);
    } catch (e) {
        console.log('Forgot Password failed (expected if Brevo credentials are dummy):', e.response?.data || e.message);
    }

    console.log('\n--- 3. TESTING INCIDENT REPORT (CLOUDINARY) ---');
    try {
        // Create dummy valid PNG file
        const base64Png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
        fs.writeFileSync('dummy.png', Buffer.from(base64Png, 'base64'));
        
        const form = new FormData();
        form.append('report_text', 'Suspicious activity on main server');
        form.append('evidence', fs.createReadStream('dummy.png'));
        
        const res = await axios.post(`${NODE_API}/incidents`, form, {
            headers: { ...form.getHeaders(), Authorization: `Bearer ${token}` }
        });
        console.log('Incident reported:', res.data);
    } catch (e) {
        console.log('Incident failed (expected if Cloudinary credentials are dummy):', e.response?.data || e.message);
    }

    console.log('\n--- 4. TESTING MITIGATION ENDPOINT ---');
    try {
        const res = await axios.post(`${NODE_API}/incidents/mitigation`, {
            report_text: 'Suspicious login attempt from unknown IP address detected in active deployment zone.',
            rank_level: 5,
            is_active_deployment: true
        }, {
            headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Mitigation Response:', res.data.playbook ? 'Generated successfully via Groq!' : res.data);
    } catch (e) {
        console.log('Mitigation failed:', e.response?.data || e.message);
    }
}

runTests();
