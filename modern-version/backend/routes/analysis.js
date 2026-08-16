const express = require('express');
const router = express.Router();
const multer = require('multer');
const { PDFParse } = require('pdf-parse');
const axios = require('axios');
const mongoose = require('mongoose');
const Analysis = require('../models/Analysis');

// In-memory fallback database in case MongoDB is down
const memoryHistory = [];

// Setup multer memory storage for PDF resume uploads
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 5 * 1024 * 1024 } // 5MB limit
});

// Helper to extract compatibility score from generated markdown response
function extractScore(markdownText) {
    const scoreRegex = /(?:Compatibility Score|Compatibility Score:.*?)\s*\*?\*?\[?(\d+)\]?%/i;
    const match = markdownText.match(scoreRegex);
    if (match && match[1]) {
        return parseInt(match[1], 10);
    }
    
    const fallbackRegex = /(\d+)%/;
    const fallbackMatch = markdownText.match(fallbackRegex);
    if (fallbackMatch && fallbackMatch[1]) {
        return parseInt(fallbackMatch[1], 10);
    }
    return 0;
}

// Helper to extract job title from JD text
function extractJobTitle(jdText) {
    if (!jdText) return 'Job Match Analysis';
    const lines = jdText.trim().split('\n');
    if (lines.length > 0 && lines[0].trim().length > 0) {
        const candidate = lines[0].trim().replace(/[#*_-]/g, '').trim();
        return candidate.length > 60 ? candidate.substring(0, 60) + '...' : candidate;
    }
    return 'Job Match Analysis';
}

// @route   POST /api/analyze
// @desc    Analyze JD vs Resume (supports optional file upload)
router.post('/analyze', upload.single('resumeFile'), async (req, res) => {
    try {
        let { jdText, resumeText } = req.body;
        let fileName = '';

        if (req.file) {
            fileName = req.file.originalname;
            try {
                const pdfParser = new PDFParse({ data: req.file.buffer });
                const pdfData = await pdfParser.getText();
                resumeText = pdfData.text;
                if (!resumeText || resumeText.trim().length === 0) {
                    return res.status(400).json({ success: false, message: 'Could not extract text from the uploaded PDF.' });
                }
            } catch (pdfErr) {
                console.error('PDF parsing error:', pdfErr);
                return res.status(400).json({ success: false, message: `PDF parsing error: ${pdfErr.message}` });
            }
        }

        if (!jdText || !jdText.trim()) {
            return res.status(400).json({ success: false, message: 'Job Description is required.' });
        }
        if (!resumeText || !resumeText.trim()) {
            return res.status(400).json({ success: false, message: 'Resume text is required.' });
        }

        const systemPrompt = `You are a senior technical recruiter with 15 years of experience screening resumes against job descriptions for engineering roles.

Rules you must follow:
- Output ONLY valid JSON matching the exact schema requested.
- No preamble, no closing remarks, no formatting other than valid JSON.
- Never invent a numeric "probability of being hired" — only use the four qualitative tiers: Low, Medium, High, Strong.
- Base the compatibility_score strictly on the real overlap between the resume content and the job description requirements — be realistic.
- recommended_projects must NOT repeat any project already listed in the resume text.
- Every gap listed must have a corresponding recommended_project addressing it.
- Keep list items concise and descriptive (under 20 words each).`;

        const userPrompt = `Analyze the RESUME against the JOB DESCRIPTION below.
You MUST respond with a single JSON object matching exactly this schema:
{
  "compatibility_score": integer_between_0_and_100,
  "verdict": "string (1-sentence overview of overall alignment)",
  "strengths": [
    "string (first key strength matching the JD)",
    "string (second key strength matching the JD)",
    "string (third key strength matching the JD)"
  ],
  "gaps": [
    "string (first critical gap/missing requirement from JD)",
    "string (second critical gap/missing requirement from JD)"
  ],
  "recommended_projects": [
    {
      "name": "string (name of a NEW project the candidate should build)",
      "tech_stack": "string (comma-separated tech stack for this project)",
      "why": "string (explain how it specifically closes the first critical gap)"
    },
    {
      "name": "string (name of a second NEW project to build)",
      "tech_stack": "string (comma-separated tech stack)",
      "why": "string (explain how it specifically closes the second critical gap)"
    }
  ],
  "keywords_to_add": ["string (first missing keyword)", "string (second missing keyword)"],
  "format_tip": "string (one concise formatting/ATS tip)",
  "current_chance_tier": "Low | Medium | High | Strong (select exactly one)",
  "current_chance_reasoning": "string (reasoning for current chance based on resume)",
  "projected_chance_tier": "Low | Medium | High | Strong (select exactly one)",
  "projected_chance_reasoning": "string (reasoning for projected chance after building these projects and closing gaps)"
}

---
JOB DESCRIPTION:
${jdText.substring(0, 2000)}

---
RESUME:
${resumeText.substring(0, 3000)}

---
Produce ONLY the filled-in JSON object above. Do not output any other text or explanation.`;

        const ollamaEndpoint = process.env.AI_ENDPOINT || 'http://localhost:11434/api/generate';
        const modelName = process.env.AI_MODEL_NAME || 'qwen2.5:1.5b';
        const timeout = parseInt(process.env.AI_TIMEOUT || '600000', 10);

        console.log(`Sending JSON query to Ollama (${modelName})...`);
        const response = await axios.post(ollamaEndpoint, {
            model: modelName,
            prompt: userPrompt,
            system: systemPrompt,
            stream: false,
            format: 'json',
            options: {
                temperature: 0.2,
                top_p: 0.9,
                num_predict: 500,
                repeat_penalty: 1.1
            }
        }, { timeout });

        const resStr = response.data.response || '{}';
        let cleaned = resStr.trim();
        if (cleaned.startsWith('```json')) {
            cleaned = cleaned.substring(7);
        } else if (cleaned.startsWith('```')) {
            cleaned = cleaned.substring(3);
        }
        if (cleaned.endsWith('```')) {
            cleaned = cleaned.substring(0, cleaned.length - 3);
        }
        cleaned = cleaned.trim();

        let resDict;
        try {
            resDict = JSON.parse(cleaned);
        } catch (e) {
            const match = resStr.match(/\{[\s\S]*\}/);
            if (match) {
                try {
                    resDict = JSON.parse(match[0]);
                } catch (e2) {
                    throw new Error(`Failed to parse extracted JSON block: ${e2.message}. Raw response: ${resStr}`);
                }
            } else {
                throw new Error(`Failed to parse AI response as JSON: ${e.message}. Raw response: ${resStr}`);
            }
        }

        let compatibilityScore = parseInt(resDict.compatibility_score || 0, 10);
        if (isNaN(compatibilityScore)) compatibilityScore = 0;
        compatibilityScore = Math.max(0, Math.min(100, compatibilityScore));

        const verdict = (resDict.verdict || '').trim();

        const strengthsList = Array.isArray(resDict.strengths) ? resDict.strengths : [];
        const strengthsBullets = strengthsList.map(item => `🔹 ${String(item).trim()}`).join('\n\n') || '🔹 None identified.';

        const gapsList = Array.isArray(resDict.gaps) ? resDict.gaps : [];
        const gapsBullets = gapsList.map(item => `🔹 ${String(item).trim()}`).join('\n\n') || '🔹 None identified.';

        const projectsList = Array.isArray(resDict.recommended_projects) ? resDict.recommended_projects : [];
        const projectsBullets = projectsList.map(p => {
            if (p && typeof p === 'object') {
                const pName = (p.name || 'New Project').trim();
                const pStack = (p.tech_stack || 'Tech Stack').trim();
                const pWhy = (p.why || 'Closes gap').trim();
                return `🔹 **${pName}** (${pStack}) — ${pWhy}`;
            }
            return `🔹 ${String(p).trim()}`;
        }).join('\n\n') || '🔹 None recommended.';

        const keywordsList = Array.isArray(resDict.keywords_to_add) ? resDict.keywords_to_add : [];
        const keywords = keywordsList.map(kw => String(kw).trim()).join(', ') || 'None missing.';

        const formatTip = (resDict.format_tip || '').trim();

        const currentChanceTier = (resDict.current_chance_tier || 'Low').trim();
        const currentChanceReasoning = (resDict.current_chance_reasoning || '').trim();
        const projectedChanceTier = (resDict.projected_chance_tier || 'Medium').trim();
        const projectedChanceReasoning = (resDict.projected_chance_reasoning || '').trim();

        const resultMarkdown = `1. 🚀 **Compatibility Score**: ${compatibilityScore}%
🔹 ${verdict}

2. 🎯 **Core Strengths & Alignment**:
${strengthsBullets}

3. 💡 **Critical Skill Gaps**:
${gapsBullets}

4. 🏗️ **Recommended Projects**:
${projectsBullets}

5. 🛠️ **ATS Optimization & Resume Fixes**:
🔹 **Keywords to add**: ${keywords}
🔹 **Format tip**: ${formatTip}

6. 📈 **Chances**: ${currentChanceTier} → after improvements: ${projectedChanceTier}
🔹 **Now**: ${currentChanceReasoning}
🔹 **After**: ${projectedChanceReasoning}`;

        const jobTitle = extractJobTitle(jdText);

        const analysisData = {
            jobTitle,
            jobDescription: jdText,
            resumeText,
            fileName,
            compatibilityScore,
            resultMarkdown,
            createdAt: new Date()
        };

        let savedItem;

        // Check database connection state
        if (mongoose.connection.readyState === 1) {
            const analysis = new Analysis(analysisData);
            savedItem = await analysis.save();
            console.log('Successfully saved analysis to MongoDB.');
        } else {
            // Memory fallback
            savedItem = {
                _id: new mongoose.Types.ObjectId().toString(),
                ...analysisData
            };
            memoryHistory.unshift(savedItem);
            console.log('Saved analysis to in-memory fallback list.');
        }

        res.json({
            success: true,
            score: compatibilityScore,
            resultMarkdown,
            item: savedItem
        });

    } catch (err) {
        console.error('API analyze error:', err.message);
        let errorMsg = 'An error occurred during analysis.';
        if (err.code === 'ECONNREFUSED') {
            errorMsg = `Could not connect to Ollama. Run 'ollama serve' and ensure the model '${process.env.AI_MODEL_NAME || 'qwen2.5:1.5b'}' is pulled.`;
        } else if (err.code === 'ETIMEOUT' || err.message.includes('timeout')) {
            errorMsg = 'Ollama request timed out. Please try with shorter inputs.';
        }
        res.status(500).json({ success: false, message: errorMsg, details: err.message });
    }
});

// @route   GET /api/history
// @desc    Get all past compatibility checks
router.get('/history', async (req, res) => {
    try {
        if (mongoose.connection.readyState === 1) {
            const items = await Analysis.find().sort({ createdAt: -1 });
            res.json({ success: true, count: items.length, items });
        } else {
            // Return memory list
            res.json({ success: true, count: memoryHistory.length, items: memoryHistory });
        }
    } catch (err) {
        console.error('API history error:', err.message);
        res.status(500).json({ success: false, message: 'Server error retrieving history.' });
    }
});

// @route   DELETE /api/history/:id
// @desc    Delete a compatibility check record
router.delete('/history/:id', async (req, res) => {
    try {
        const id = req.params.id;
        let found = false;

        if (mongoose.connection.readyState === 1) {
            const item = await Analysis.findById(id);
            if (item) {
                await item.deleteOne();
                found = true;
                console.log(`Deleted analysis ${id} from MongoDB.`);
            }
        }

        // Always clean from memory fallback as well
        const initialLen = memoryHistory.length;
        const index = memoryHistory.findIndex(item => item._id === id);
        if (index !== -1) {
            memoryHistory.splice(index, 1);
            found = true;
            console.log(`Deleted analysis ${id} from in-memory list.`);
        }

        if (!found) {
            return res.status(404).json({ success: false, message: 'Record not found' });
        }

        res.json({ success: true, message: 'Record removed successfully' });
    } catch (err) {
        console.error('API delete error:', err.message);
        res.status(500).json({ success: false, message: 'Server error removing record.' });
    }
});

module.exports = router;
