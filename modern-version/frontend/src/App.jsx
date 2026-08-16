import React, { useState, useEffect, useRef } from 'react';
import { 
  Briefcase, 
  FileText, 
  Upload, 
  Trash2, 
  History, 
  ChevronRight, 
  Sun, 
  Moon, 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  Sparkles,
  RefreshCw,
  X,
  FileCheck
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000/api';

// Custom Markdown parser component for simple formatting (bold, bullets, scores, headers)
const MarkdownViewer = ({ markdown }) => {
  if (!markdown) return null;

  const parseText = (text) => {
    // Escape simple HTML
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Handle headers
    html = html.replace(/^### (.*?)$/gm, '<h3 class="markdown-h3">$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2 class="markdown-h2">$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1 class="markdown-h1">$1</h1>');

    // Handle bold text
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Handle bullet lists
    html = html.replace(/^🔹 (.*?)$/gm, '<li class="markdown-li"><span class="bullet-emoji">🔹</span> $1</li>');
    html = html.replace(/^- (.*?)$/gm, '<li class="markdown-li"><span class="bullet-emoji">🔹</span> $1</li>');

    // Paragraph splits
    html = html.split('\n\n').map(p => {
      if (p.trim().startsWith('<h') || p.trim().startsWith('<li')) {
        return p;
      }
      return `<p class="markdown-p">${p.replace(/\n/g, '<br/>')}</p>`;
    }).join('');

    return html;
  };

  return (
    <div 
      className="markdown-content" 
      dangerouslySetInnerHTML={{ __html: parseText(markdown) }} 
    />
  );
};

function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved || 'dark';
  });

  const [jdText, setJdText] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [uploadMode, setUploadMode] = useState('type'); // 'type' or 'upload'
  
  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [history, setHistory] = useState([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const fileInputRef = useRef(null);

  // Sync theme class with body
  useEffect(() => {
    document.body.className = theme === 'dark' ? 'dark-theme' : 'light-theme';
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Fetch analysis history
  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/history`);
      const data = await response.json();
      if (data.success) {
        setHistory(data.items);
      }
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Only PDF resumes are supported.');
        setResumeFile(null);
        return;
      }
      setError('');
      setResumeFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Only PDF resumes are supported.');
        return;
      }
      setError('');
      setResumeFile(file);
    }
  };

  const loadSample = () => {
    setJdText(`Senior Software Engineer - Full Stack (Python & React)

Qualifications & Skills:
- 5+ years of software engineering experience.
- Strong proficiency in Python, FastAPI, and Django backends.
- Professional experience with React, Redux, and modern frontend styling.
- Hands-on experience with MongoDB, PostgreSQL, and query optimization.
- Deep understanding of REST APIs, Docker containerization, and AWS hosting.
- Experience with testing suites (pytest, jest) and CI/CD pipelines.`);

    setResumeText(`John Doe - Full Stack Developer
Email: john.doe@email.com | Github: github.com/johndoe

Summary:
Innovative Software Developer with 4 years of experience building modern web applications. Focused on writing scalable backend systems in Python and interactive user interfaces using React.

Experience:
Web Engineer @ TechFlow Corp (2022 - Present)
- Engineered high-traffic REST APIs using Python, FastAPI, and PostgreSQL.
- Developed dynamic frontends using React.js and Tailwind CSS.
- Deployed microservices utilizing Docker containers on AWS ECS.

Skills:
- Languages: Python, JavaScript, SQL, HTML/CSS
- Frameworks: React, FastAPI, Express
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Docker, Git, AWS (S3, EC2)`);
    setUploadMode('type');
    setResumeFile(null);
  };

  const clearInputs = () => {
    setJdText('');
    setResumeText('');
    setResumeFile(null);
    setAnalysisResult(null);
    setError('');
    setSuccess(false);
  };

  const runAnalysis = async () => {
    setError('');
    setSuccess(false);
    setAnalysisResult(null);

    // Validate inputs
    if (!jdText.trim()) {
      setError('Please provide a Job Description.');
      return;
    }
    if (uploadMode === 'type' && !resumeText.trim()) {
      setError('Please write or paste your resume content.');
      return;
    }
    if (uploadMode === 'upload' && !resumeFile) {
      setError('Please upload a PDF resume.');
      return;
    }

    setLoading(true);
    setProgressStep('Preparing resume parsing...');

    try {
      const formData = new FormData();
      formData.append('jdText', jdText);

      if (uploadMode === 'upload') {
        setProgressStep('Parsing PDF resume text...');
        formData.append('resumeFile', resumeFile);
      } else {
        setProgressStep('Packaging request...');
        formData.append('resumeText', resumeText);
      }

      // Simulate steps for smooth visual progression
      setTimeout(() => {
        if (loading) setProgressStep('Connecting to Ollama & Qwen AI...');
      }, 1500);

      setTimeout(() => {
        if (loading) setProgressStep('Analyzing core strengths & alignment...');
      }, 5000);

      setTimeout(() => {
        if (loading) setProgressStep('Synthesizing compatibility report...');
      }, 15000);

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Failed to complete analysis.');
      }

      setAnalysisResult(data);
      setSuccess(true);
      fetchHistory(); // Refresh history list

    } catch (err) {
      console.error(err);
      setError(err.message || 'Server connection failed.');
    } finally {
      setLoading(false);
      setProgressStep('');
    }
  };

  const loadHistoryItem = (item) => {
    setAnalysisResult({
      score: item.compatibilityScore,
      resultMarkdown: item.resultMarkdown,
      item
    });
    setJdText(item.jobDescription);
    if (item.fileName) {
      setUploadMode('upload');
      setResumeFile({ name: item.fileName });
      setResumeText('');
    } else {
      setUploadMode('type');
      setResumeText(item.resumeText);
      setResumeFile(null);
    }
    setIsHistoryOpen(false); // Close sidebar
    // Scroll to results
    setTimeout(() => {
      document.getElementById('result-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const deleteHistoryItem = async (e, id) => {
    e.stopPropagation(); // Avoid triggering loading the item
    try {
      const response = await fetch(`${API_BASE_URL}/history/${id}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      if (data.success) {
        setHistory(prev => prev.filter(item => item._id !== id));
        if (analysisResult?.item?._id === id) {
          setAnalysisResult(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  return (
    <div className="app-container">
      {/* ── HEADER ── */}
      <header className="main-header glass-card">
        <div className="header-brand">
          <div className="brand-title">
            <h1>CareerFit AI</h1>
            <span className="rocket-icon">🚀</span>
          </div>
          <p className="brand-subtitle">Developed by Allen Charles</p>
        </div>

        <div className="header-controls">
          <a href="http://127.0.0.1:7860" className="btn-secondary redirect-btn">
            Click here to Access the Basic Version
          </a>
          <button 
            className="control-btn" 
            onClick={() => setIsHistoryOpen(true)}
            title="Analysis History"
          >
            <History size={18} />
          </button>
          <button 
            className="control-btn theme-toggle" 
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={18} className="sun-icon" /> : <Moon size={18} className="moon-icon" />}
          </button>
        </div>
      </header>

      {/* ── MAIN CONTENT GRID ── */}
      <main className="content-grid">
        {/* ── LEFT CARD: JOB DESCRIPTION ── */}
        <section className="input-section glass-card">
          <div className="section-header">
            <div className="header-icon-wrap jd-color">
              <Briefcase size={20} />
            </div>
            <h2>Job Description</h2>
          </div>

          <div className="textarea-container">
            <textarea
              placeholder="Paste the full target job description details here..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="custom-textarea"
            />
          </div>

          <div className="action-row">
            <button className="btn-secondary" onClick={loadSample}>
              <Sparkles size={14} className="sparkle-icon" />
              Load Sample JD & Resume
            </button>
          </div>
        </section>

        {/* ── RIGHT CARD: RESUME CONTENT ── */}
        <section className="input-section glass-card">
          <div className="section-header">
            <div className="header-icon-wrap resume-color">
              <FileText size={20} />
            </div>
            <h2>Your Resume</h2>
          </div>

          {/* Mode Switch Tabs */}
          <div className="tab-row">
            <button 
              className={`tab-btn ${uploadMode === 'type' ? 'tab-active' : ''}`}
              onClick={() => setUploadMode('type')}
            >
              <RefreshCw size={14} className="tab-icon" />
              Type Resume
            </button>
            <button 
              className={`tab-btn ${uploadMode === 'upload' ? 'tab-active' : ''}`}
              onClick={() => setUploadMode('upload')}
            >
              <Upload size={14} className="tab-icon" />
              Upload PDF
            </button>
          </div>

          <div className="textarea-container">
            {uploadMode === 'type' ? (
              <textarea
                placeholder="Type or paste your complete resume text here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                className="custom-textarea"
              />
            ) : (
              <div 
                className={`drag-drop-zone ${resumeFile ? 'file-loaded' : ''}`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="application/pdf"
                  style={{ display: 'none' }}
                />
                
                {resumeFile ? (
                  <div className="file-info-wrap">
                    <FileCheck size={48} className="file-icon-success" />
                    <h3>{resumeFile.name}</h3>
                    <p>PDF Document Loaded</p>
                    <button 
                      className="btn-text-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        setResumeFile(null);
                      }}
                    >
                      Remove File
                    </button>
                  </div>
                ) : (
                  <div className="drag-info-wrap">
                    <Upload size={48} className="upload-arrow-icon" />
                    <h3>Drag & Drop your Resume PDF here</h3>
                    <p>or click to browse from files (Max 5MB)</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="action-row flex-end">
            <button className="btn-danger-outline" onClick={clearInputs}>
              Clear All
            </button>
          </div>
        </section>
      </main>

      {/* ── ANALYZE TRIGGER BAR ── */}
      <div className="trigger-bar">
        <button 
          className={`btn-primary btn-large analyze-btn ${loading ? 'loading' : ''}`}
          onClick={runAnalysis}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="spinner" size={20} />
              <span>Analyzing Resume...</span>
            </>
          ) : (
            <>
              <Sparkles size={20} className="sparkle-icon" />
              <span>Analyze Resume Compatibility</span>
            </>
          )}
        </button>
      </div>

      {/* ── LOADING DIALOG & STEPS ── */}
      {loading && (
        <div className="loading-backdrop">
          <div className="loading-modal glass-card">
            <Loader2 className="spinner spinner-large" size={48} />
            <h2>Running Compatibility Check</h2>
            <div className="step-badge">
              <span className="pulse-indicator"></span>
              {progressStep}
            </div>
            <p className="loading-notice">
              Ollama is computing local weights. This may take up to 2 minutes on CPU. Please keep this window open.
            </p>
          </div>
        </div>
      )}

      {/* ── ERROR DISPLAY ── */}
      {error && (
        <div className="notification-toast error-toast glass-card">
          <AlertCircle size={20} className="toast-icon" />
          <div className="toast-body">
            <h4>Analysis Failed</h4>
            <p>{error}</p>
          </div>
          <button className="toast-close" onClick={() => setError('')}><X size={16} /></button>
        </div>
      )}

      {/* ── ANALYSIS REPORT DISPLAY ── */}
      {analysisResult && (
        <section id="result-section" className="result-section glass-card fade-in">
          <div className="result-header">
            <div className="score-badge-circle">
              <div className="score-value">{analysisResult.score}%</div>
              <div className="score-label">Match Score</div>
            </div>
            <div className="result-header-text">
              <h2>AI Compatibility Report</h2>
              <p>Generated using local Qwen 2.5 Intelligence</p>
            </div>
          </div>

          <div className="result-body">
            <MarkdownViewer markdown={analysisResult.resultMarkdown} />
          </div>
        </section>
      )}

      {/* ── HISTORY SIDEBAR PANEL ── */}
      <div className={`history-sidebar-wrapper ${isHistoryOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-backdrop" onClick={() => setIsHistoryOpen(false)}></div>
        <aside className="history-sidebar glass-card">
          <div className="sidebar-header">
            <div className="header-title">
              <History size={18} />
              <h3>Analysis History</h3>
            </div>
            <button className="control-btn close-sidebar" onClick={() => setIsHistoryOpen(false)}>
              <X size={18} />
            </button>
          </div>

          <div className="sidebar-list">
            {history.length === 0 ? (
              <div className="sidebar-empty">
                <p>No past analysis reports found.</p>
              </div>
            ) : (
              history.map((item) => (
                <div 
                  key={item._id} 
                  className="history-item glass-card"
                  onClick={() => loadHistoryItem(item)}
                >
                  <div className="item-left">
                    <div className={`score-badge-sm ${item.compatibilityScore > 75 ? 'score-high' : item.compatibilityScore > 50 ? 'score-mid' : 'score-low'}`}>
                      {item.compatibilityScore}%
                    </div>
                  </div>
                  <div className="item-body">
                    <h4>{item.jobTitle}</h4>
                    <p>{new Date(item.createdAt).toLocaleDateString()} {item.fileName && `• ${item.fileName}`}</p>
                  </div>
                  <button 
                    className="btn-icon-delete"
                    onClick={(e) => deleteHistoryItem(e, item._id)}
                    title="Delete record"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
