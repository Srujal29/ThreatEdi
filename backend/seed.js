const axios = require('axios');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');

const PYTHON_API_URL = 'http://127.0.0.1:8000/api';

async function seedUsers() {
    try {
        const passwordHash1 = await bcrypt.hash('password123', 10);
        const passwordHash2 = await bcrypt.hash('admin456', 10);

        const users = [
            {
                user_id: uuidv4(),
                full_name: 'Officer John Doe',
                email: 'john.doe@army.mil',
                service_number: 'SN-1001',
                password_hash: passwordHash1,
                user_type: 'Active',
                rank_id: 8, // Lieutenant
                unit_id: 1, // 1st Armoured Division
            },
            {
                user_id: uuidv4(),
                full_name: 'Commander Jane Smith',
                email: 'jane.smith@army.mil',
                service_number: 'SN-2002',
                password_hash: passwordHash2,
                user_type: 'Active',
                rank_id: 11, // Lieutenant Colonel
                unit_id: 4, // 15 Corps
            }
        ];

        for (const user of users) {
            try {
                await axios.post(`${PYTHON_API_URL}/internal/users`, user);
                console.log('Inserted user:', user.email);
            } catch (err) {
                console.error('Error inserting user:', user.email, err.response ? err.response.data : err.message);
            }
        }
    } catch (e) {
        console.error("Seed error", e);
    }
}

seedUsers();
