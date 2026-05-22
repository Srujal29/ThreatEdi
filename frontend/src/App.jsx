import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldAlert, Shield, ShieldCheck, Mail, Lock, User, Hash, Award, 
  ArrowRight, CheckSquare, Loader, FolderOpen, AlertOctagon, AlertTriangle, 
  Info, WifiOff, FileSearch, Eye, LogOut, CheckCircle, Upload, Paperclip, 
  FileText, ScanEye, RefreshCw, Layers, ExternalLink
} from 'lucide-react';
import { Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
} from 'chart.js';

// Register ChartJS plugins
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
);

function App() {
  // --- STATE ---
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [ranks, setRanks] = useState([]);
  const [units, setUnits] = useState([]);
  const [userIncidents, setUserIncidents] = useState([]);
  const [adminIncidents, setAdminIncidents] = useState([]);
  
  // Navigation states
  const [authForm, setAuthForm] = useState('login'); // login | register | reset
  const [resetStep, setResetStep] = useState(1); // 1: request, 2: verify/reset
  const [activeTab, setActiveTab] = useState('tab-user-report'); // tab-user-report | tab-user-list | tab-admin-dashboard | tab-admin-incidents
  
  // Routing states
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);
  
  // Login form fields
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Register form fields
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regService, setRegService] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regRankId, setRegRankId] = useState('');
  const [regUnitId, setRegUnitId] = useState('');
  const [regUserType, setRegUserType] = useState('Active');
  const [registerLoading, setRegisterLoading] = useState(false);

  // Reset password form fields
  const [resetEmail, setResetEmail] = useState('');
  const [resetOtp, setResetOtp] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  // Report Incident form fields
  const [reportText, setReportText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [liveAnalysis, setLiveAnalysis] = useState(null);
  const [reportRankId, setReportRankId] = useState('');
  const [reportUnitId, setReportUnitId] = useState('');

  // Sync user details to default rank and unit reporting overrides
  useEffect(() => {
    if (user) {
      if (user.rank_id) setReportRankId(user.rank_id.toString());
      if (user.unit_id) setReportUnitId(user.unit_id.toString());
    }
  }, [user]);
  
  // Admin Filter States
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  
  // Details/Inspector Modal States
  const [showModal, setShowModal] = useState(false);
  const [modalIncident, setModalIncident] = useState(null);
  const [modalReporter, setModalReporter] = useState(null);
  const [modalPlaybook, setModalPlaybook] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalStatusSelect, setModalStatusSelect] = useState('Pending');
  const [modalUpdatingStatus, setModalUpdatingStatus] = useState(false);

  // Toasts
  const [toasts, setToasts] = useState([]);
  
  const fileInputRef = useRef(null);

  // --- HELPERS ---
  const showToast = (title, message, type = 'info') => {
    const id = Date.now() + Math.random().toString();
    setToasts(prev => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  const getRiskClass = (score) => {
    if (score < 3.0) return 'low';
    if (score < 6.0) return 'medium';
    if (score < 8.0) return 'high';
    return 'critical';
  };

  // --- EFFECT TRIGGERS ---
  useEffect(() => {
    // 1. Check local session
    const storedToken = sessionStorage.getItem('token');
    const storedUser = sessionStorage.getItem('user');
    
    // 2. Fetch static metadata ranks and units
    const fetchMetadata = async () => {
      try {
        const ranksRes = await fetch('/api/auth/ranks');
        const unitsRes = await fetch('/api/auth/units');
        if (ranksRes.ok && unitsRes.ok) {
          setRanks(await ranksRes.json());
          setUnits(await unitsRes.json());
        }
      } catch (err) {
        console.error('Failed to pre-load configuration resources:', err);
      }
    };

    fetchMetadata();

    if (storedToken && storedUser) {
      const parsedUser = JSON.parse(storedUser);
      const isAdminPath = window.location.pathname.startsWith('/admin');
      const isUserAdmin = parsedUser.user_type === 'Admin' || parsedUser.user_type === 'CRT';
      
      if (isAdminPath && !isUserAdmin) {
        setToken(null);
        setUser(null);
        sessionStorage.clear();
      } else if (!isAdminPath && isUserAdmin) {
        navigateTo('/admin');
        setToken(storedToken);
        setUser(parsedUser);
        setActiveTab('tab-admin-dashboard');
      } else {
        setToken(storedToken);
        setUser(parsedUser);
        if (isUserAdmin) {
          setActiveTab('tab-admin-dashboard');
        } else {
          setActiveTab('tab-user-report');
        }
      }
    }
  }, []);

  useEffect(() => {
    if (!token || !user) return;
    const isAdminPath = currentPath.startsWith('/admin');
    const isUserAdmin = user.user_type === 'Admin' || user.user_type === 'CRT';

    if (isAdminPath && !isUserAdmin) {
      showToast('Access Denied', 'Restricted to CRT/Admin accounts. Redirecting to User Portal...', 'error');
      navigateTo('/');
    } else if (!isAdminPath && isUserAdmin) {
      showToast('Redirecting', 'Admin session active. Loading Command Center...', 'info');
      navigateTo('/admin');
    }
  }, [currentPath, token, user]);

  // Sync user or admin incident data when authenticated or switching tab
  useEffect(() => {
    if (!token || !user) return;
    
    if (user.user_type === 'Admin' || user.user_type === 'CRT') {
      if (activeTab === 'tab-admin-dashboard' || activeTab === 'tab-admin-incidents') {
        fetchAdminIncidents();
      }
    } else {
      if (activeTab === 'tab-user-list') {
        fetchUserIncidents();
      }
    }
  }, [token, user, activeTab, filterStatus, filterPriority]);

  // --- API CALLS ---
  
  // USER API: fetch all user's reports
  const fetchUserIncidents = async () => {
    try {
      const res = await fetch('/api/incidents', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // filter client-side for logged-in user
        setUserIncidents(data.filter(inc => inc.user_id === user.id));
      }
    } catch (err) {
      showToast('Sync Failed', 'Failed to synchronize user incident logs.', 'error');
    }
  };

  // ADMIN API: fetch all reports in queue
  const fetchAdminIncidents = async () => {
    try {
      let query = [];
      if (filterStatus) query.push(`status=${filterStatus}`);
      if (filterPriority) query.push(`priority=${filterPriority}`);
      const queryString = query.length > 0 ? `?${query.join('&')}` : '';
      
      const res = await fetch(`/api/incidents${queryString}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setAdminIncidents(await res.json());
      }
    } catch (err) {
      showToast('Sync Failed', 'Failed to synchronize admin incident stream.', 'error');
    }
  };

  // Auth: handle Login
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) return;
    setLoginLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        const isUserAdmin = data.user.user_type === 'Admin' || data.user.user_type === 'CRT';
        const isAdminPath = currentPath.startsWith('/admin');
        
        if (isAdminPath && !isUserAdmin) {
          showToast('Login Failed', 'Authorized CRT/Admin credentials required on this portal.', 'error');
          return;
        }
        if (!isAdminPath && isUserAdmin) {
          setToken(data.token);
          setUser(data.user);
          sessionStorage.setItem('token', data.token);
          sessionStorage.setItem('user', JSON.stringify(data.user));
          showToast('Authentication Successful', `Welcome back, Admin ${data.user.name}. Redirecting to CRT Command Center...`, 'success');
          navigateTo('/admin');
          setActiveTab('tab-admin-dashboard');
          return;
        }

        setToken(data.token);
        setUser(data.user);
        sessionStorage.setItem('token', data.token);
        sessionStorage.setItem('user', JSON.stringify(data.user));
        
        showToast('Authentication Successful', `Welcome back, ${data.user.name}.`, 'success');
        
        if (isUserAdmin) {
          setActiveTab('tab-admin-dashboard');
        } else {
          setActiveTab('tab-user-report');
        }
      } else {
        showToast('Login Failed', data.error || 'Invalid credentials.', 'error');
      }
    } catch (err) {
      showToast('Network Error', 'Failed to contact authentication gateway.', 'error');
    } finally {
      setLoginLoading(false);
    }
  };

  // Auth: handle Registration
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!regName || !regEmail || !regService || !regPassword || !regRankId || !regUnitId) {
      showToast('Fields Required', 'Please fill out all registration fields.', 'warning');
      return;
    }
    if (regPassword.length < 6) {
      showToast('Validation Error', 'Password must be at least 6 characters.', 'warning');
      return;
    }

    setRegisterLoading(true);

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: regName,
          email: regEmail,
          service_number: regService,
          password: regPassword,
          user_type: regUserType,
          rank_id: regRankId,
          unit_id: regUnitId
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        showToast('Registration Successful', 'Account enrolled. You can now login.', 'success');
        setAuthForm('login');
        setLoginEmail(regEmail);
        setLoginPassword('');
      } else {
        showToast('Enrolment Refused', data.error || 'Failed to register account.', 'error');
      }
    } catch (err) {
      showToast('Network Error', 'Registration service is offline.', 'error');
    } finally {
      setRegisterLoading(false);
    }
  };

  // Forgot password OTP Request
  const handleRequestOTP = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      showToast('Email Required', 'Please enter your registered email address.', 'warning');
      return;
    }
    setResetLoading(true);

    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('OTP Dispatched', data.message || 'OTP code sent to email.', 'success');
        setResetStep(2);
      } else {
        showToast('OTP Delivery Failed', data.error || 'Could not dispatch OTP.', 'error');
      }
    } catch (err) {
      showToast('Network Error', 'OTP server is temporarily unreachable.', 'error');
    } finally {
      setResetLoading(false);
    }
  };

  // Verify OTP and Reset Password
  const handleVerifyAndReset = async (e) => {
    e.preventDefault();
    if (!resetOtp || !resetNewPassword) {
      showToast('Inputs Required', 'Both OTP code and a new password are required.', 'warning');
      return;
    }
    if (resetNewPassword.length < 6) {
      showToast('Validation Error', 'Password must be at least 6 characters.', 'warning');
      return;
    }
    setResetLoading(true);

    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail, otp_code: resetOtp, new_password: resetNewPassword })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Password Updated', 'Your security keys have been reset. Login with new credentials.', 'success');
        setAuthForm('login');
        setResetStep(1);
        setLoginEmail(resetEmail);
      } else {
        showToast('Reset Denied', data.error || 'Incorrect OTP code or verify timeout.', 'error');
      }
    } catch (err) {
      showToast('Network Error', 'Could not complete password update.', 'error');
    } finally {
      setResetLoading(false);
    }
  };

  // Submit Incident Report
  const handleReportIncident = async (e) => {
    e.preventDefault();
    if (!reportText) {
      showToast('Input Required', 'Please describe the incident details.', 'warning');
      return;
    }
    setReportLoading(true);
    setLiveAnalysis({ loading: true });

    const formData = new FormData();
    formData.append('report_text', reportText);
    if (selectedFile) {
      formData.append('evidence', selectedFile);
    }
    if (reportRankId) {
      formData.append('rank_id', reportRankId);
    }
    if (reportUnitId) {
      formData.append('unit_id', reportUnitId);
    }

    try {
      const res = await fetch('/api/incidents', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Report Evaluated', 'Pipeline completed successfully.', 'success');
        setLiveAnalysis(data.incident_data);
        
        // Reset inputs
        setReportText('');
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        showToast('Evaluation Error', data.error || 'Failed to complete incident analysis.', 'error');
        setLiveAnalysis(null);
      }
    } catch (err) {
      showToast('Network Error', 'Failed to dispatch report to gateway.', 'error');
      setLiveAnalysis(null);
    } finally {
      setReportLoading(false);
    }
  };

  // Logout
  const handleLogout = () => {
    setToken(null);
    setUser(null);
    sessionStorage.clear();
    showToast('Session Terminated', 'Securely logged out of the ThreatEdi Command center.', 'info');
    setAuthForm('login');
  };

  // Drag and Drop File Handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      showToast('Size Bound Warning', 'The selected file exceeds the 10MB transmission limit.', 'error');
      return;
    }
    setSelectedFile(file);
  };

  // Inspect Modal detail fetcher
  const openIncidentModal = async (incidentId) => {
    setShowModal(true);
    setModalLoading(true);
    setModalIncident(null);
    setModalReporter(null);
    setModalPlaybook(null);

    try {
      // 1. Get incident details
      const incRes = await fetch(`/api/incidents/${incidentId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!incRes.ok) throw new Error("Incident not found.");
      const inc = await incRes.json();
      setModalIncident(inc);
      setModalStatusSelect(inc.status);

      // 2. Fetch reporter metadata in parallel
      let reporterData = null;
      try {
        const uRes = await fetch(`/api/auth/users/${inc.user_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (uRes.ok) reporterData = await uRes.json();
      } catch (err) {
        console.error('Failed to fetch reporter info', err);
      }
      setModalReporter(reporterData);

      // 3. Fetch mitigation playbook
      try {
        const playRes = await fetch('/api/incidents/mitigation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            report_text: inc.report_text,
            rank_level: reporterData?.rank?.hierarchy_level || 1,
            is_active_deployment: reporterData?.unit?.is_active_deployment || false
          })
        });
        if (playRes.ok) {
          const pData = await playRes.json();
          setModalPlaybook(pData.playbook || pData);
        }
      } catch (err) {
        console.error('Failed to get playbook', err);
      }
    } catch (err) {
      showToast('Retransmit Failure', 'Failed to retrieve detailed parameters.', 'error');
      setShowModal(false);
    } finally {
      setModalLoading(false);
    }
  };

  // Update incident status (CRT admin update)
  const handleUpdateStatus = async () => {
    if (!modalIncident) return;
    setModalUpdatingStatus(true);
    try {
      const res = await fetch(`/api/incidents/${modalIncident.incident_id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ new_status: modalStatusSelect })
      });
      if (res.ok) {
        showToast('Record Updated', `Status changed to ${modalStatusSelect}.`, 'success');
        setShowModal(false);
        // Refresh grids
        if (user.user_type === 'Admin' || user.user_type === 'CRT') {
          fetchAdminIncidents();
        } else {
          fetchUserIncidents();
        }
      } else {
        const data = await res.json();
        showToast('Update Denied', data.error || 'Failed to update status.', 'error');
      }
    } catch (err) {
      showToast('Network Error', 'Could not patch incident status.', 'error');
    } finally {
      setModalUpdatingStatus(false);
    }
  };

  // --- CHART CALCULATORS ---
  const getCategoryChartData = () => {
    const counts = {};
    adminIncidents.forEach(inc => {
      const cat = inc.ml_category || 'Phishing';
      counts[cat] = (counts[cat] || 0) + 1;
    });

    const labels = Object.keys(counts);
    const data = Object.values(counts);

    return {
      labels: labels.length > 0 ? labels : ['No Incidents'],
      datasets: [{
        data: data.length > 0 ? data : [0],
        backgroundColor: [
          '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b'
        ],
        borderWidth: 1,
        borderColor: '#0c111e'
      }]
    };
  };

  const getPriorityChartData = () => {
    const counts = { Low: 0, Medium: 0, High: 0, Critical: 0 };
    adminIncidents.forEach(inc => {
      const pri = inc.priority_level || 'Medium';
      if (counts.hasOwnProperty(pri)) counts[pri] += 1;
    });

    return {
      labels: ['Low', 'Medium', 'High', 'Critical'],
      datasets: [{
        label: 'Severity Level',
        data: [counts.Low, counts.Medium, counts.High, counts.Critical],
        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
        borderWidth: 0,
        borderRadius: 4
      }]
    };
  };

  // --- RENDER FUNCTIONS ---
  
  // Render Auth module
  const renderAuthScreen = () => {
    const isAdminPath = currentPath.startsWith('/admin');

    return (
      <div className="auth-wrapper flex-center">
        <div className={`auth-card glass-panel ${isAdminPath ? 'admin-theme' : ''}`}>
          <div className="auth-header text-center">
            <div className="logo-icon-wrapper">
              <ShieldAlert className={`logo-icon ${isAdminPath ? 'text-red' : 'text-emerald'} animate-pulse`} />
            </div>
            <h1>{isAdminPath ? 'RESTRICTED ACCESS' : 'THREATEDI'}</h1>
            <p className="subtitle text-slate">
              {isAdminPath 
                ? 'AUTHORIZED CRT PERSONNEL ONLY' 
                : 'Secure Cyber Incident Command Portal'}
            </p>
          </div>

          {authForm === 'login' && (
            <form onSubmit={handleLoginSubmit} className="auth-form active">
              <h2>{isAdminPath ? 'CRT Authentication' : 'Sign In'}</h2>
              <div className="form-group">
                <label htmlFor="login-email"><Mail className="inline-icon" /> Email Address</label>
                <input 
                  type="email" 
                  id="login-email" 
                  required 
                  placeholder="name.lastname@army.mil" 
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="login-password"><Lock className="inline-icon" /> Password</label>
                <input 
                  type="password" 
                  id="login-password" 
                  required 
                  placeholder="••••••••" 
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                />
              </div>
              <button type="submit" className={`btn ${isAdminPath ? 'btn-danger' : 'btn-primary'} btn-block`} disabled={loginLoading}>
                <span>{loginLoading ? 'Authorizing...' : (isAdminPath ? 'Authorize Command' : 'Access Portal')}</span>
                {loginLoading ? <Loader className="animate-spin inline-icon" /> : <ArrowRight className="inline-icon" />}
              </button>
              
              <div className="auth-footer flex-between">
                {!isAdminPath ? (
                  <>
                    <a href="#" className="link-text text-sm" onClick={(e) => { e.preventDefault(); setAuthForm('reset'); setResetStep(1); }}>Forgot Password?</a>
                    <a href="#" className="link-text text-sm font-semibold text-emerald" onClick={(e) => { e.preventDefault(); setAuthForm('register'); }}>Register Account</a>
                  </>
                ) : (
                  <>
                    <a href="#" className="link-text text-sm" onClick={(e) => { e.preventDefault(); setAuthForm('reset'); setResetStep(1); }}>Forgot Password?</a>
                    <a href="#" className="link-text text-sm font-semibold text-red" onClick={(e) => { e.preventDefault(); navigateTo('/'); }}>User Portal</a>
                  </>
                )}
              </div>

              {!isAdminPath && (
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <a href="#" className="link-text text-xs text-slate" onClick={(e) => { e.preventDefault(); navigateTo('/admin'); }}>
                    CRT / CSOC Admin Gateway
                  </a>
                </div>
              )}
            </form>
          )}

          {authForm === 'register' && !isAdminPath && (
            <form onSubmit={handleRegisterSubmit} className="auth-form active">
              <h2>Account Registration</h2>
              <div className="form-grid">
                <div className="form-group">
                  <label><User className="inline-icon" /> Full Name</label>
                  <input 
                    type="text" 
                    required 
                    placeholder="Officer Jane Doe"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label><Mail className="inline-icon" /> Email</label>
                  <input 
                    type="email" 
                    required 
                    placeholder="jane.smith@army.mil"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label><Hash className="inline-icon" /> Service Number</label>
                  <input 
                    type="text" 
                    required 
                    placeholder="SN-XXXX"
                    value={regService}
                    onChange={(e) => setRegService(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label><Lock className="inline-icon" /> Password</label>
                  <input 
                    type="password" 
                    required 
                    placeholder="Min 6 characters"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label><Award className="inline-icon" /> Military Rank</label>
                  <select required value={regRankId} onChange={(e) => setRegRankId(e.target.value)}>
                    <option value="" disabled>Select Rank...</option>
                    {ranks.map(r => (
                      <option key={r.rank_id} value={r.rank_id}>{r.rank_name} (Level {r.hierarchy_level})</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label><Shield className="inline-icon" /> Deployment Unit</label>
                  <select required value={regUnitId} onChange={(e) => setRegUnitId(e.target.value)}>
                    <option value="" disabled>Select Unit...</option>
                    {units.map(u => (
                      <option key={u.unit_id} value={u.unit_id}>{u.unit_name} ({u.base_location})</option>
                    ))}
                  </select>
                </div>

              </div>
              <button type="submit" className="btn btn-primary btn-block margin-top-md" disabled={registerLoading}>
                <span>{registerLoading ? 'Enrolling Agent...' : 'Register Account'}</span>
                {registerLoading ? <Loader className="animate-spin inline-icon" /> : <ShieldCheck className="inline-icon" />}
              </button>
              <div className="auth-footer text-center">
                <a href="#" className="link-text text-sm" onClick={(e) => { e.preventDefault(); setAuthForm('login'); }}>Already have an account? Sign In</a>
              </div>
            </form>
          )}

          {authForm === 'reset' && (
            <div className="auth-form active">
              <h2>Password Recovery Wizard</h2>
              {resetStep === 1 ? (
                <form onSubmit={handleRequestOTP} className="wizard-step active">
                  <p className="step-desc text-slate">Enter your registered email address below. We will verify your identity credentials and dispatch an SMTP OTP verification token.</p>
                  <div className="form-group">
                    <label><Mail className="inline-icon" /> Email Address</label>
                    <input 
                      type="email" 
                      required 
                      placeholder="name.lastname@army.mil"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary btn-block" disabled={resetLoading}>
                    <span>{resetLoading ? 'Transmitting OTP...' : 'Send OTP Code'}</span>
                    {resetLoading ? <Loader className="animate-spin inline-icon" /> : <ArrowRight className="inline-icon" />}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyAndReset} className="wizard-step active">
                  <p className="step-desc text-slate">Enter the OTP verification code sent to <strong>{resetEmail}</strong> and specify your new authentication credentials.</p>
                  <div className="form-group">
                    <label><Hash className="inline-icon" /> OTP Token</label>
                    <input 
                      type="text" 
                      required 
                      placeholder="XXXXXX"
                      value={resetOtp}
                      onChange={(e) => setResetOtp(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label><Lock className="inline-icon" /> New Security Password</label>
                    <input 
                      type="password" 
                      required 
                      placeholder="Min 6 characters"
                      value={resetNewPassword}
                      onChange={(e) => setResetNewPassword(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary btn-block" disabled={resetLoading}>
                    <span>{resetLoading ? 'Validating Token...' : 'Reset Password'}</span>
                    {resetLoading ? <Loader className="animate-spin inline-icon" /> : <ShieldCheck className="inline-icon" />}
                  </button>
                </form>
              )}
              <div className="auth-footer text-center">
                <a href="#" className="link-text text-sm" onClick={(e) => { e.preventDefault(); setAuthForm('login'); }}>Back to Login screen</a>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render Dashboard
  const renderDashboard = () => {
    const isCrt = user?.user_type === 'Admin' || user?.user_type === 'CRT';

    

    
    return (
      <div className="dashboard-wrapper">
        {/* Main Header */}
        <header className="main-header glass-panel flex-between">
          <div className="header-brand flex-align-center">
            <Shield className="brand-icon text-emerald" />
            <span className="brand-title">THREATEDI</span>
            {isCrt ? (
              <span className="badge badge-crt ml-sm text-xs font-semibold">CRT MONITOR</span>
            ) : (
              <span className="badge badge-active ml-sm text-xs font-semibold">ACTIVE USER</span>
            )}
          </div>
          
          <div className="header-actions flex-align-center">

            <button className="btn-icon btn-danger" onClick={handleLogout} title="Close Grid Connection">
              <LogOut />
            </button>
          </div>
        </header>

        {/* Dashboard Frame */}
        <div className="dashboard-body">
          {/* Sidebar */}
          <aside className="sidebar glass-panel">


            {/* Sidebar Navigation Options */}
            <nav className="sidebar-nav">
              <ul>
                {!isCrt ? (
                  <>
                    <li>
                      <button 
                        className={`nav-btn ${activeTab === 'tab-user-report' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tab-user-report')}
                      >
                        <ShieldAlert />
                        <span>File Report</span>
                      </button>
                    </li>
                    <li>
                      <button 
                        className={`nav-btn ${activeTab === 'tab-user-list' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tab-user-list')}
                      >
                        <FolderOpen />
                        <span>My Repositories</span>
                        <span className="pill bg-slate">{userIncidents.length}</span>
                      </button>
                    </li>
                  </>
                ) : (
                  <>
                    <li>
                      <button 
                        className={`nav-btn ${activeTab === 'tab-admin-dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tab-admin-dashboard')}
                      >
                        <Layers />
                        <span>Command Dashboard</span>
                      </button>
                    </li>
                    <li>
                      <button 
                        className={`nav-btn ${activeTab === 'tab-admin-incidents' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tab-admin-incidents')}
                      >
                        <ShieldAlert />
                        <span>Incident stream</span>
                        <span className="pill bg-red">{adminIncidents.filter(i => i.status === 'Pending').length}</span>
                      </button>
                    </li>
                  </>
                )}
              </ul>
            </nav>
          </aside>

          {/* Main Viewport Content area */}
          <main className="main-content">
            {/* View Tab 1: User Submit Report */}
            {!isCrt && activeTab === 'tab-user-report' && (
              <div className="viewport-tab active">
                <div className="viewport-header">
                  <h2>Report Cyber Event Narrative</h2>
                  <p className="text-slate">Submit anomalous system details to the ML pipeline. Upload files for Gemini security evaluation.</p>
                </div>
                
                <div className="grid-2x1 gap-md margin-top-md">
                  {/* Form Box */}
                  <div className="glass-panel pad-md flex-column gap-sm">
                    <form onSubmit={handleReportIncident}>
                      <div className="form-group">
                        <label htmlFor="report-text">Threat Narrative Description</label>
                        <textarea 
                          id="report-text" 
                          rows="6"
                          required
                          placeholder="Describe the anomalous events, phishing details, payload signatures, or suspicious behaviors noticed..."
                          value={reportText}
                          onChange={(e) => setReportText(e.target.value)}
                        ></textarea>
                      </div>

                      {/* File Selection Zone */}
                      <div className="form-group">
                        <label>Threat Evidence / Logs Screenshot</label>
                        {!selectedFile ? (
                          <div 
                            className={`drop-zone ${isDragOver ? 'dragover' : ''}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current.click()}
                          >
                            <Upload className="upload-icon text-emerald animate-pulse margin-bottom-sm" style={{ margin: '0 auto 8px' }} />
                            <p className="text-sm font-semibold">Drag & Drop Evidence Screenshot or Click to Browse</p>
                            <p className="text-xs text-slate margin-top-xs">Supported formats: JPEG, PNG, PDF, MP4 (Max size: 10MB)</p>
                          </div>
                        ) : (
                          <div className="file-preview-card flex-between">
                            <div className="flex-align-center gap-sm">
                              {selectedFile.type.startsWith('video/') ? (
                                <FileText className="text-blue" />
                              ) : selectedFile.type === 'application/pdf' ? (
                                <FileText className="text-red" />
                              ) : (
                                <Paperclip className="text-emerald" />
                              )}
                              <div className="flex-column">
                                <span className="text-sm font-semibold" style={{ wordBreak: 'break-all' }}>{selectedFile.name}</span>
                                <span className="text-xs text-slate">{(selectedFile.size / 1024).toFixed(1)} KB</span>
                              </div>
                            </div>
                            <button 
                              type="button" 
                              className="btn btn-danger btn-sm"
                              onClick={() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                            >
                              Clear
                            </button>
                          </div>
                        )}
                        <input 
                          type="file" 
                          ref={fileInputRef} 
                          className="hidden" 
                          onChange={handleFileChange}
                          accept="image/*,video/mp4,application/pdf"
                        />
                      </div>

                      <div className="grid-equal gap-sm margin-top-md" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '16px' }}>
                        <div className="form-group">
                          <label htmlFor="report-rank">Reporting Officer Rank Override</label>
                          <select
                            id="report-rank"
                            value={reportRankId}
                            onChange={(e) => setReportRankId(e.target.value)}
                            required
                          >
                            <option value="">Select Rank</option>
                            {ranks.map((r) => (
                              <option key={r.rank_id} value={r.rank_id}>
                                {r.rank_name} (Level {r.hierarchy_level})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label htmlFor="report-unit">Posting Unit Override</label>
                          <select
                            id="report-unit"
                            value={reportUnitId}
                            onChange={(e) => setReportUnitId(e.target.value)}
                            required
                          >
                            <option value="">Select Unit</option>
                            {units.map((u) => (
                              <option key={u.unit_id} value={u.unit_id}>
                                {u.unit_name} ({u.is_active_deployment ? 'Combat Active' : 'Base Area'})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <button type="submit" className="btn btn-primary btn-block margin-top-md" disabled={reportLoading}>
                        <span>{reportLoading ? 'Processing through ML Pipeline...' : 'Submit Incident to ML Pipeline'}</span>
                        {reportLoading ? <Loader className="animate-spin inline-icon" /> : <ShieldAlert className="inline-icon" />}
                      </button>
                    </form>
                  </div>

                  {/* Dynamic Pipeline Output */}
                  <div className="flex-column" id="live-analysis-panel">
                    {!liveAnalysis ? (
                      <div className="glass-panel pad-md banner-glow flex-column flex-center text-center height-100 flex-1 min-height-300">
                        <Shield className="large-icon text-slate animate-pulse" style={{ width: '48px', height: '48px', margin: '0 auto 8px' }} />
                        <h3 className="margin-top-sm">Threat Prediction Engine</h3>
                        <p className="text-slate text-sm max-width-300 margin-top-xs">Fill out the incident form and submit to invoke the neural net classifier, risk model, and dynamic remediation generator.</p>
                      </div>
                    ) : liveAnalysis.loading ? (
                      <div className="glass-panel pad-md banner-glow flex-column flex-center text-center height-100 flex-1 min-height-300">
                        <Loader className="large-icon text-emerald animate-spin" style={{ width: '48px', height: '48px', margin: '0 auto 8px' }} />
                        <h3 className="margin-top-sm">Analyzing Incident Vectors...</h3>
                        <p className="text-slate text-sm max-width-300 margin-top-xs">Applying neural models for classification and calculating risk indices in real-time.</p>
                      </div>
                    ) : (
                      <div className="glass-panel pad-md banner-glow flex-column gap-md report-feedback-card">
                        <div className="flex-between">
                          <span className="text-xs uppercase font-bold tracking-wider text-slate">Pipeline Results</span>
                          <span className="status-pill pending">Pending Investigation</span>
                        </div>
                        
                        <div className="glass-panel pad-md flex-column gap-xs" style={{ borderLeft: '4px solid var(--color-emerald)', background: 'rgba(16, 185, 129, 0.03)', borderColor: 'rgba(16, 185, 129, 0.15)' }}>
                          <span className="text-xs uppercase font-bold tracking-wider text-slate">AI Threat Classification Signature</span>
                          <div className="flex-align-center gap-sm flex-wrap">
                            <h3 className="text-emerald text-xl font-bold uppercase" style={{ letterSpacing: '0.05em' }}>
                              {liveAnalysis.incident?.inferred_threat_type || liveAnalysis.incident?.ml_category || 'Unclassified Threat'}
                            </h3>
                            <span className="badge badge-active" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                              {liveAnalysis.incident?.ml_confidence ? `${(liveAnalysis.incident.ml_confidence * 100).toFixed(0)}% AI Confidence` : 'N/A'}
                            </span>
                          </div>
                          <p className="text-xs text-slate" style={{ marginTop: '4px', lineHeight: '1.4' }}>
                            The pipeline has analyzed your report narrative and classified the primary vector as a <strong>{liveAnalysis.incident?.inferred_threat_type || liveAnalysis.incident?.ml_category || 'unknown'}</strong> threat {liveAnalysis.incident?.inferred_threat_type && liveAnalysis.incident?.inferred_threat_type !== liveAnalysis.incident?.ml_category && `(ML Category: ${liveAnalysis.incident.ml_category})`}.
                          </p>
                        </div>
                        
                        <div className="flex-row gap-md">
                          <div className="info-card flex-1">
                            <span className="label">Priority</span>
                            <span className="value text-red font-bold">{liveAnalysis.incident?.priority_level}</span>
                          </div>
                          <div className="info-card flex-1">
                            <span className="label">Risk Index</span>
                            <span className={`value risk-level-badge ${getRiskClass(liveAnalysis.incident?.risk_score)}`}>{liveAnalysis.incident?.risk_score.toFixed(1)}/10</span>
                          </div>
                        </div>

                        {/* Severity Risk Score Breakdown */}
                        {liveAnalysis.risk_breakdown?.risk_details?.breakdown && (
                          <div className="glass-panel pad-md" style={{ backgroundColor: 'rgba(255,255,255,0.01)', borderColor: 'rgba(255,255,255,0.03)', marginTop: '8px' }}>
                            <h4 className="text-xs uppercase font-bold text-emerald mb-sm"><ScanEye className="inline-icon" style={{ width: '12px', height: '12px' }} /> Severity Risk Score Breakdown</h4>
                            <div className="flex-column gap-sm" style={{ marginTop: '8px' }}>
                              <div className="breakdown-row">
                                <div className="flex-between text-xs text-slate">
                                  <span>ML Classifier Confidence (40% weight)</span>
                                  <span className="font-bold">{liveAnalysis.risk_breakdown.risk_details.breakdown.ml_confidence_component.toFixed(1)}/4.0</span>
                                </div>
                                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                                  <div className="progress-bar-fill" style={{ height: '100%', width: `${(liveAnalysis.risk_breakdown.risk_details.breakdown.ml_confidence_component / 4.0) * 100}%`, background: 'var(--color-emerald)' }}></div>
                                </div>
                              </div>
                              <div className="breakdown-row">
                                <div className="flex-between text-xs text-slate">
                                  <span>Officer Rank Level (20% weight)</span>
                                  <span className="font-bold">{liveAnalysis.risk_breakdown.risk_details.breakdown.rank_component.toFixed(1)}/2.0</span>
                                </div>
                                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                                  <div className="progress-bar-fill" style={{ height: '100%', width: `${(liveAnalysis.risk_breakdown.risk_details.breakdown.rank_component / 2.0) * 100}%`, background: '#3b82f6' }}></div>
                                </div>
                              </div>
                              <div className="breakdown-row">
                                <div className="flex-between text-xs text-slate">
                                  <span>Unit Deployment Status (20% weight)</span>
                                  <span className="font-bold">{liveAnalysis.risk_breakdown.risk_details.breakdown.deployment_component.toFixed(1)}/2.0</span>
                                </div>
                                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                                  <div className="progress-bar-fill" style={{ height: '100%', width: `${(liveAnalysis.risk_breakdown.risk_details.breakdown.deployment_component / 2.0) * 100}%`, background: '#eab308' }}></div>
                                </div>
                              </div>
                              <div className="breakdown-row">
                                <div className="flex-between text-xs text-slate">
                                  <span>Critical Keyword Severity (20% weight - {liveAnalysis.risk_breakdown.risk_details.breakdown.keyword_hits} hits)</span>
                                  <span className="font-bold">{liveAnalysis.risk_breakdown.risk_details.breakdown.severity_component.toFixed(1)}/2.0</span>
                                </div>
                                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                                  <div className="progress-bar-fill" style={{ height: '100%', width: `${(liveAnalysis.risk_breakdown.risk_details.breakdown.severity_component / 2.0) * 100}%`, background: '#ef4444' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        <div className="flex-column gap-xs">
                          <h4 className="font-semibold text-sm">Dynamic Mitigation Playbook</h4>
                          <ul className="playbook-steps-list">
                            {liveAnalysis.playbook?.action_steps?.map((step, idx) => (
                              <li key={idx} className="playbook-step-item">
                                <CheckSquare className="text-emerald" style={{ width: '16px', height: '16px', flexShrink: 0, marginTop: '2px' }} />
                                <span>{step}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        {liveAnalysis.incident?.evidence_analysis && (
                          <div className="evidence-analysis-box flex-column gap-xs">
                            <h4 className="font-semibold text-sm text-slate"><Eye className="inline-icon text-purple" style={{ width: '14px', height: '14px' }} /> AI Evidence Analysis</h4>
                            <p className="text-xs text-slate" style={{ lineHeight: '1.5' }}>{liveAnalysis.incident?.evidence_analysis}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* View Tab 2: User History Log list */}
            {!isCrt && activeTab === 'tab-user-list' && (
              <div className="viewport-tab active">
                <div className="viewport-header flex-between">
                  <div>
                    <h2>Incident Log Repositories</h2>
                    <p className="text-slate">Manage your active reported incident streams and consult recommendation files.</p>
                  </div>
                  <button className="btn btn-secondary" onClick={fetchUserIncidents}>
                    <RefreshCw className="inline-icon" />
                    <span>Synchronize</span>
                  </button>
                </div>

                <div className="flex-column gap-md margin-top-md" id="user-incidents-container">
                  {userIncidents.length === 0 ? (
                    <div className="glass-panel pad-lg text-center text-slate">
                      <FolderOpen className="large-icon margin-bottom-sm" style={{ width: '48px', height: '48px', margin: '0 auto 8px' }} />
                      <h3>No Incidents Filed</h3>
                      <p className="text-sm margin-top-xs">Your repository is clear. Report any threats via the form tab.</p>
                    </div>
                  ) : (
                    userIncidents.map(inc => {
                      const riskClass = getRiskClass(inc.risk_score);
                      const dateStr = new Date(inc.timestamp).toLocaleString();
                      
                      return (
                        <div key={inc.incident_id} className={`glass-panel pad-md incident-summary-card ${inc.status.toLowerCase()}`}>
                          <div className="incident-summary-header">
                            <div>
                              <span className="text-xs uppercase font-bold tracking-wider text-slate block" style={{ fontSize: '0.65rem' }}>Identified Threat Category</span>
                              <h3 className="font-bold text-emerald uppercase" style={{ letterSpacing: '0.02em', marginTop: '2px' }}>
                                {inc.inferred_threat_type || inc.ml_category || 'Unclassified Threat'}
                              </h3>
                              {inc.inferred_threat_type && inc.inferred_threat_type !== inc.ml_category && (
                                <span className="text-xs text-slate block" style={{ fontSize: '0.7rem' }}>ML Signature: {inc.ml_category}</span>
                              )}
                              <span className="incident-date">{dateStr}</span>
                            </div>
                            <div className="flex-align-center gap-xs">
                              <span className={`risk-level-badge ${riskClass}`}>Risk: {inc.risk_score.toFixed(1)}</span>
                              <span className="risk-level-badge critical">{inc.priority_level}</span>
                              <span className={`status-pill ${inc.status.toLowerCase()}`}>{inc.status}</span>
                            </div>
                          </div>
                          
                          <div className="incident-details-box text-slate">
                            <strong>Incident Context Narrative:</strong><br/>
                            {inc.report_text}
                          </div>
                          
                          <div className="flex-row gap-sm margin-top-md">
                            <button className="btn btn-emerald btn-sm" onClick={() => openIncidentModal(inc.incident_id)}>
                              <FileSearch className="inline-icon" style={{ width: '14px', height: '14px' }} /> Inspect Playbook
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {/* View Tab 3: Admin Analytics Command Center */}
            {isCrt && activeTab === 'tab-admin-dashboard' && (
              <div className="viewport-tab active">
                <div className="viewport-header">
                  <h2>CSOC Cybersecurity Analytics Center</h2>
                  <p className="text-slate">System wide threat aggregates, risk distribution indexes, and classification charts.</p>
                </div>

                {/* Dashboard Stats metrics */}
                <div className="stats-grid margin-top-md">
                  <div className="glass-panel stat-card flex-align-center gap-md">
                    <div className="stat-icon bg-blue-dim flex-center">
                      <Layers style={{ width: '24px', height: '24px' }} />
                    </div>
                    <div>
                      <span className="stat-label">Total Logs</span>
                      <span className="stat-val" id="stat-total">{adminIncidents.length}</span>
                    </div>
                  </div>
                  <div className="glass-panel stat-card flex-align-center gap-md">
                    <div className="stat-icon bg-red-dim flex-center">
                      <ShieldAlert style={{ width: '24px', height: '24px' }} />
                    </div>
                    <div>
                      <span className="stat-label">Pending Alerts</span>
                      <span className="stat-val" id="stat-pending">{adminIncidents.filter(i => i.status === 'Pending').length}</span>
                    </div>
                  </div>
                  <div className="glass-panel stat-card flex-align-center gap-md">
                    <div className="stat-icon bg-emerald-dim flex-center">
                      <ShieldCheck style={{ width: '24px', height: '24px' }} />
                    </div>
                    <div>
                      <span className="stat-label">Resolved Threats</span>
                      <span className="stat-val" id="stat-resolved">{adminIncidents.filter(i => i.status === 'Resolved').length}</span>
                    </div>
                  </div>
                  <div className="glass-panel stat-card flex-align-center gap-md">
                    <div className="stat-icon bg-yellow-dim flex-center">
                      <AlertTriangle style={{ width: '24px', height: '24px' }} />
                    </div>
                    <div>
                      <span className="stat-label">Average Risk</span>
                      <span className="stat-val" id="stat-avg-risk">
                        {adminIncidents.length > 0 
                          ? (adminIncidents.reduce((sum, i) => sum + i.risk_score, 0) / adminIncidents.length).toFixed(1)
                          : '0.0'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                {/* Chart components */}
                <div className="grid-2x1 gap-md margin-top-md">
                  <div className="glass-panel chart-wrapper">
                    <div className="chart-title">
                      <Layers className="text-emerald" style={{ width: '18px', height: '18px' }} />
                      <span>Threat Category Distribution</span>
                    </div>
                    <div style={{ height: '240px', position: 'relative' }}>
                      <Doughnut data={getCategoryChartData()} options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'right',
                            labels: { color: '#94a3b8', font: { family: 'Outfit' } }
                          }
                        }
                      }} />
                    </div>
                  </div>
                  <div className="glass-panel chart-wrapper">
                    <div className="chart-title">
                      <ShieldAlert className="text-red" style={{ width: '18px', height: '18px' }} />
                      <span>Severity Classification Counts</span>
                    </div>
                    <div style={{ height: '240px', position: 'relative' }}>
                      <Bar data={getPriorityChartData()} options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false }
                        },
                        scales: {
                          x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', font: { family: 'Outfit' } }
                          },
                          y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8', font: { family: 'Outfit' }, stepSize: 1 }
                          }
                        }
                      }} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* View Tab 4: Admin Incident Stream logs grid */}
            {isCrt && activeTab === 'tab-admin-incidents' && (
              <div className="viewport-tab active">
                <div className="viewport-header flex-between flex-wrap gap-sm">
                  <div>
                    <h2>Cyber Security Event logs Queue</h2>
                    <p className="text-slate">Master threat feed from deployed army systems. Inspect parameters and update logs.</p>
                  </div>
                  
                  <div className="flex-align-center gap-sm flex-wrap">
                    <div className="flex-align-center gap-xs">
                      <label className="text-xs text-slate uppercase font-semibold">Status:</label>
                      <select 
                        className="filter-select select-sm" 
                        style={{ width: 'auto', padding: '6px 12px' }}
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                      >
                        <option value="">All Statuses</option>
                        <option value="Pending">Pending</option>
                        <option value="Investigating">Investigating</option>
                        <option value="Resolved">Resolved</option>
                      </select>
                    </div>

                    <div className="flex-align-center gap-xs">
                      <label className="text-xs text-slate uppercase font-semibold">Priority:</label>
                      <select 
                        className="filter-select select-sm" 
                        style={{ width: 'auto', padding: '6px 12px' }}
                        value={filterPriority}
                        onChange={(e) => setFilterPriority(e.target.value)}
                      >
                        <option value="">All Priorities</option>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                        <option value="Critical">Critical</option>
                      </select>
                    </div>

                    <button className="btn btn-secondary" onClick={fetchAdminIncidents}>
                      <RefreshCw className="inline-icon" />
                      <span>Fetch Queue</span>
                    </button>
                  </div>
                </div>

                <div className="glass-panel table-responsive margin-top-md">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Reporter / Timestamp</th>
                        <th>Classification Narrative</th>
                        <th>Risk Score</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Operations</th>
                      </tr>
                    </thead>
                    <tbody id="admin-queue-tbody">
                      {adminIncidents.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="text-center pad-lg text-slate">
                            <CheckCircle className="large-icon margin-bottom-sm text-emerald" style={{ width: '48px', height: '48px', margin: '0 auto 8px' }} />
                            <h3>Incident Queue Empty</h3>
                            <p className="text-sm">No threats match current filter parameters or the stream is empty.</p>
                          </td>
                        </tr>
                      ) : (
                        adminIncidents.map(inc => {
                          const riskClass = getRiskClass(inc.risk_score);
                          const dateStr = new Date(inc.timestamp).toLocaleString();
                          const snippet = inc.report_text.substring(0, 75) + (inc.report_text.length > 75 ? '...' : '');
                          
                          return (
                            <tr key={inc.incident_id}>
                              <td>
                                <div className="user-summary">
                                  <span className="name">Reporter #{inc.user_id.substring(0, 8)}</span>
                                  <span className="sub">Logged: {dateStr}</span>
                                </div>
                              </td>
                              <td>
                                <span className="text-xs uppercase font-bold tracking-wider text-slate block" style={{ fontSize: '0.65rem' }}>Threat Vector</span>
                                <span className="font-bold text-sm block text-emerald uppercase" style={{ letterSpacing: '0.02em', marginTop: '2px' }}>
                                  {inc.inferred_threat_type || inc.ml_category || 'Phishing'}
                                </span>
                                {inc.inferred_threat_type && inc.inferred_threat_type !== inc.ml_category && (
                                  <span className="text-xs text-slate block" style={{ fontSize: '0.7rem' }}>ML Signature: {inc.ml_category}</span>
                                )}
                                <span className="text-xs text-slate">{snippet}</span>
                              </td>
                              <td>
                                <span className={`risk-level-badge ${riskClass}`}>{inc.risk_score.toFixed(1)}/10</span>
                              </td>
                              <td>
                                <span className="risk-level-badge critical">{inc.priority_level}</span>
                              </td>
                              <td>
                                <span className={`status-pill ${inc.status.toLowerCase()}`}>{inc.status}</span>
                              </td>
                              <td>
                                <button className="btn btn-secondary btn-sm" onClick={() => openIncidentModal(inc.incident_id)}>
                                  <Eye className="inline-icon" style={{ width: '14px', height: '14px' }} /> Inspect
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </main>
        </div>

        {/* Dynamic Modal detailed Inspector popup */}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header flex-between">
                <h3 id="modal-title" style={{ fontWeight: 800, fontSize: '1.2rem', letterSpacing: '0.05em' }}>
                  {isCrt ? "CSOC Threat Incident Inspector" : "Threat Response Playbook"}
                </h3>
                <button className="btn-icon" onClick={() => setShowModal(false)}>&times;</button>
              </div>

              <div id="modal-details-container" style={{ marginTop: '16px' }}>
                {modalLoading ? (
                  <div className="text-center pad-lg text-slate">
                    <Loader className="large-icon animate-spin margin-bottom-sm text-emerald" style={{ width: '48px', height: '48px', margin: '0 auto 8px' }} />
                    <p>Consulting mitigation database...</p>
                  </div>
                ) : (
                  <div className="flex-column gap-md animated scale-up">
                    
                    {/* Reporter Context parameters */}
                    {isCrt && modalReporter && (
                      <div className="glass-panel pad-md" style={{ backgroundColor: 'rgba(255,255,255,0.01)', borderColor: 'rgba(255,255,255,0.03)' }}>
                        <h4 className="text-xs uppercase font-bold text-emerald mb-sm"><User className="inline-icon" style={{ width: '12px', height: '12px' }} /> Reporter Profile Details</h4>
                        <div className="inspector-header-grid">
                          <div className="info-card">
                            <span className="label">Name</span>
                            <span className="value text-sm font-semibold">{modalReporter.full_name}</span>
                          </div>
                          <div className="info-card">
                            <span className="label">Service Number</span>
                            <span className="value text-sm font-semibold">{modalReporter.service_number}</span>
                          </div>
                          <div className="info-card">
                            <span className="label">Rank / Hierarchy</span>
                            <span className="value text-sm font-semibold">{modalReporter.rank?.rank_name || 'Sepoy'} (Level {modalReporter.rank?.hierarchy_level || 1})</span>
                          </div>
                          <div className="info-card">
                            <span className="label">Unit Location</span>
                            <span className="value text-sm font-semibold">{modalReporter.unit?.unit_name || 'Cyber Group'}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Threat classification signature banner */}
                    <div className="glass-panel pad-md banner-glow flex-column gap-xs" style={{ borderLeft: '4px solid var(--color-emerald)', background: 'rgba(16, 185, 129, 0.03)', borderColor: 'rgba(16, 185, 129, 0.15)', marginBottom: '16px' }}>
                      <span className="text-xs uppercase font-bold tracking-wider text-slate">AI Threat Classification Signature</span>
                      <div className="flex-align-center gap-sm flex-wrap">
                        <h3 className="text-emerald text-xl font-bold uppercase" style={{ letterSpacing: '0.05em' }}>
                          {modalIncident?.inferred_threat_type || modalIncident?.ml_category || 'UNCLASSIFIED THREAT'}
                        </h3>
                        <span className="badge badge-active" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                          {modalIncident?.ml_confidence ? `${(modalIncident.ml_confidence * 100).toFixed(0)}% AI Confidence` : 'Verified Classification'}
                        </span>
                      </div>
                      {modalIncident?.inferred_threat_type && modalIncident?.inferred_threat_type !== modalIncident?.ml_category && (
                        <span className="text-xs text-slate block" style={{ fontSize: '0.75rem', marginTop: '-4px' }}>
                          ML Core Signature: <strong className="text-slate">{modalIncident.ml_category}</strong>
                        </span>
                      )}
                      <p className="text-xs text-slate" style={{ marginTop: '4px', lineHeight: '1.4' }}>
                        The threat detection pipeline has classified this security event vector as <strong>{modalIncident?.inferred_threat_type || modalIncident?.ml_category || 'unclassified'}</strong> with a severity index of <strong>{modalIncident?.priority_level}</strong>.
                      </p>
                    </div>

                    {/* Threat parameters summary */}
                    <div className="inspector-header-grid">
                      <div className="info-card">
                        <span className="label">Threat Category</span>
                        <span className="value text-emerald font-bold uppercase" style={{ fontSize: '0.85rem' }}>
                          {modalIncident?.inferred_threat_type || modalIncident?.ml_category || 'Threat'}
                        </span>
                      </div>
                      <div className="info-card">
                        <span className="label">Incident Severity</span>
                        <span className="value text-red font-bold">{modalIncident?.priority_level}</span>
                      </div>
                      <div className="info-card">
                        <span className="label">Risk Index</span>
                        <span className={`value risk-level-badge ${getRiskClass(modalIncident?.risk_score)}`}>{modalIncident?.risk_score?.toFixed(1)}/10</span>
                      </div>
                      <div className="info-card">
                        <span className="label">Log Status</span>
                        <span className={`status-pill ${modalIncident?.status?.toLowerCase()}`}>{modalIncident?.status}</span>
                      </div>
                    </div>

                    {/* Severity Risk Score Breakdown */}
                    {modalIncident?.risk_breakdown?.risk_details?.breakdown && (
                      <div className="glass-panel pad-md" style={{ backgroundColor: 'rgba(255,255,255,0.01)', borderColor: 'rgba(255,255,255,0.03)' }}>
                        <h4 className="text-xs uppercase font-bold text-emerald mb-sm"><ScanEye className="inline-icon" style={{ width: '12px', height: '12px' }} /> Severity Risk Score Breakdown</h4>
                        <div className="flex-column gap-sm" style={{ marginTop: '8px' }}>
                          <div className="breakdown-row">
                            <div className="flex-between text-xs text-slate">
                              <span>ML Classifier Confidence (40% weight)</span>
                              <span className="font-bold">{modalIncident.risk_breakdown.risk_details.breakdown.ml_confidence_component.toFixed(1)}/4.0</span>
                            </div>
                            <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                              <div className="progress-bar-fill" style={{ height: '100%', width: `${(modalIncident.risk_breakdown.risk_details.breakdown.ml_confidence_component / 4.0) * 100}%`, background: 'var(--color-emerald)' }}></div>
                            </div>
                          </div>
                          <div className="breakdown-row">
                            <div className="flex-between text-xs text-slate">
                              <span>Officer Rank Level (20% weight)</span>
                              <span className="font-bold">{modalIncident.risk_breakdown.risk_details.breakdown.rank_component.toFixed(1)}/2.0</span>
                            </div>
                            <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                              <div className="progress-bar-fill" style={{ height: '100%', width: `${(modalIncident.risk_breakdown.risk_details.breakdown.rank_component / 2.0) * 100}%`, background: '#3b82f6' }}></div>
                            </div>
                          </div>
                          <div className="breakdown-row">
                            <div className="flex-between text-xs text-slate">
                              <span>Unit Deployment Status (20% weight)</span>
                              <span className="font-bold">{modalIncident.risk_breakdown.risk_details.breakdown.deployment_component.toFixed(1)}/2.0</span>
                            </div>
                            <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                              <div className="progress-bar-fill" style={{ height: '100%', width: `${(modalIncident.risk_breakdown.risk_details.breakdown.deployment_component / 2.0) * 100}%`, background: '#eab308' }}></div>
                            </div>
                          </div>
                          <div className="breakdown-row">
                            <div className="flex-between text-xs text-slate">
                              <span>Critical Keyword Severity (20% weight - {modalIncident.risk_breakdown.risk_details.breakdown.keyword_hits} hits)</span>
                              <span className="font-bold">{modalIncident.risk_breakdown.risk_details.breakdown.severity_component.toFixed(1)}/2.0</span>
                            </div>
                            <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '4px', overflow: 'hidden' }}>
                              <div className="progress-bar-fill" style={{ height: '100%', width: `${(modalIncident.risk_breakdown.risk_details.breakdown.severity_component / 2.0) * 100}%`, background: '#ef4444' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) }
                    
                    {/* Narrative Description Textbox */}
                    <div className="flex-column gap-xs">
                      <h4 className="font-bold text-sm">Incident Description:</h4>
                      <p className="incident-details-box text-slate">{modalIncident?.report_text}</p>
                    </div>
                    
                    {/* Media attachments screenshot logs */}
                    {modalIncident?.evidence_url && (
                      <div className="evidence-visual-panel">
                        <h4 className="font-bold text-sm text-slate mb-sm">
                          <Paperclip className="inline-icon text-emerald" style={{ width: '14px', height: '14px' }} /> Evidence Screenshot / Attachment
                        </h4>
                        {modalIncident.evidence_url.endsWith('.mp4') ? (
                          <video src={modalIncident.evidence_url} controls className="evidence-image"></video>
                        ) : modalIncident.evidence_url.endsWith('.pdf') ? (
                          <div className="flex-align-center pad-sm gap-sm bg-slate rounded" style={{ border: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                            <FileText className="text-red" />
                            <a href={modalIncident.evidence_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-emerald flex-align-center gap-xs">
                              <span>Inspect Evidence PDF Attachment</span>
                              <ExternalLink style={{ width: '12px', height: '12px' }} />
                            </a>
                          </div>
                        ) : (
                          <img 
                            src={modalIncident.evidence_url} 
                            alt="Incident Evidence" 
                            className="evidence-image" 
                            onError={(e) => e.target.src = 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=400&q=80'}
                          />
                        )}
                      </div>
                    )}

                    {/* Gemini AI review output */}
                    {modalIncident?.evidence_analysis && (
                      <div className="evidence-analysis-box flex-column gap-xs">
                        <h4 className="font-bold text-sm text-purple flex-align-center gap-xs">
                          <ScanEye style={{ width: '16px', height: '16px' }} />
                          <span>Gemini Evidence Analysis Report</span>
                        </h4>
                        <p style={{ lineHeight: '1.5', fontSize: '0.85rem' }}>{modalIncident.evidence_analysis}</p>
                      </div>
                    )}
                    
                    {/* Playbook response actions */}
                    <div className="flex-column gap-xs border-top pad-top-md">
                      <h4 className="font-bold text-sm flex-align-center gap-xs">
                        <ShieldCheck className="text-emerald" style={{ width: '16px', height: '16px' }} />
                        <span>Recommended Mitigation Response Steps</span>
                      </h4>
                      <ul className="playbook-steps-list">
                        {modalPlaybook?.action_steps && modalPlaybook.action_steps.length > 0 ? (
                          modalPlaybook.action_steps.map((step, idx) => (
                            <li key={idx} className="playbook-step-item">
                              <CheckSquare className="text-emerald" style={{ width: '16px', height: '16px', flexShrink: 0, marginTop: '2px' }} />
                              <span>{step}</span>
                            </li>
                          ))
                        ) : (
                          <li className="playbook-step-item">
                            <Info className="text-yellow" style={{ width: '16px', height: '16px', flexShrink: 0, marginTop: '2px' }} />
                            <span>No static playbook actions. Please consult CRT officers for manual triage.</span>
                          </li>
                        )}
                      </ul>
                    </div>
                    
                    {/* Status Action updates (CRT Admin review panel) */}
                    {isCrt && (
                      <div className="glass-panel pad-md flex-between flex-wrap gap-sm margin-top-md" style={{ backgroundColor: 'rgba(255,255,255,0.01)', borderColor: 'rgba(255,255,255,0.05)' }}>
                        <div className="flex-align-center gap-xs">
                          <span className="text-sm font-bold">Current Log Status:</span>
                          <span className={`status-pill ${modalIncident?.status?.toLowerCase()}`}>{modalIncident?.status}</span>
                        </div>
                        <div className="flex-align-center gap-sm">
                          <select 
                            id="modal-status-select" 
                            className="filter-select select-sm" 
                            style={{ width: 'auto', padding: '6px 12px' }}
                            value={modalStatusSelect}
                            onChange={(e) => setModalStatusSelect(e.target.value)}
                          >
                            <option value="Pending">Pending</option>
                            <option value="Investigating">Investigating</option>
                            <option value="Resolved">Resolved</option>
                          </select>
                          <button 
                            className="btn btn-primary" 
                            onClick={handleUpdateStatus}
                            disabled={modalUpdatingStatus}
                          >
                            <span>{modalUpdatingStatus ? 'Updating...' : 'Update Status'}</span>
                          </button>
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Background Gradients & scanlines overlays */}
      <div className="glow-bg"></div>
      <div className="scanlines"></div>

      {/* Notification Toast Container */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast glass-panel ${t.type}`} style={{ pointerEvents: 'auto' }}>
            {t.type === 'success' && <CheckCircle className="text-emerald" style={{ width: '20px', height: '20px', flexShrink: 0 }} />}
            {t.type === 'error' && <AlertOctagon className="text-red" style={{ width: '20px', height: '20px', flexShrink: 0 }} />}
            {t.type === 'warning' && <AlertTriangle className="text-yellow" style={{ width: '20px', height: '20px', flexShrink: 0 }} />}
            {t.type === 'info' && <Info className="text-blue" style={{ width: '20px', height: '20px', flexShrink: 0 }} />}
            <div className="toast-message">
              <h4>{t.title}</h4>
              <p>{t.message}</p>
            </div>
          </div>
        ))}
      </div>

      {/* App wrapper */}
      <div className="app-container">
        {!token ? renderAuthScreen() : renderDashboard()}
      </div>
    </>
  );
}

export default App;
