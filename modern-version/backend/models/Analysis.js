const mongoose = require('mongoose');

const AnalysisSchema = new mongoose.Schema({
    jobTitle: {
        type: String,
        required: true,
        default: 'Job Match Analysis'
    },
    jobDescription: {
        type: String,
        required: true
    },
    resumeText: {
        type: String,
        required: true
    },
    fileName: {
        type: String,
        default: ''
    },
    compatibilityScore: {
        type: Number,
        required: true,
        default: 0
    },
    resultMarkdown: {
        type: String,
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Analysis', AnalysisSchema);
