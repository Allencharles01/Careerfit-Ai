const mongoose = require('mongoose');

const connectDB = async () => {
    try {
        const connUri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/careerfit';
        console.log(`Attempting to connect to MongoDB at ${connUri}...`);
        
        // Set short timeout so it doesn't hang forever if MongoDB is down
        const conn = await mongoose.connect(connUri, {
            serverSelectionTimeoutMS: 3000
        });
        
        console.log(`MongoDB Connected: ${conn.connection.host}`);
        return true;
    } catch (error) {
        console.warn(`\n================================================================`);
        console.warn(`⚠️  MongoDB Connection failed: ${error.message}`);
        console.warn(`👉  The system will gracefully fall back to IN-MEMORY storage.`);
        console.warn(`👉  History will persist as long as the server is running.`);
        console.warn(`================================================================\n`);
        return false;
    }
};

module.exports = connectDB;
