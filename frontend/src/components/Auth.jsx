import React, { useState } from 'react';
import { BookOpen, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const change = e => setForm({ ...form, [e.target.name]: e.target.value });
  async function submit(e) {
    e.preventDefault(); setError(''); setBusy(true);
    try {
      const { data } = await api.post(`/auth/${mode}`, form);
      localStorage.setItem('study_token', data.token);
      onLogin(data.user);
    } catch (err) { setError(err.response?.data?.message || 'Could not connect to the server.'); }
    finally { setBusy(false); }
  }
  return <main className="auth-wrap"><section className="auth-card">
    <div className="brand-mark"><BookOpen size={25}/></div><p className="eyebrow">YOUR PERSONAL LEARNING COPILOT</p>
    <h1>Study smarter.<br/><span>Not harder.</span></h1><p className="muted">Turn your notes into knowledge with AI.</p>
    <div className="tabs"><button className={mode==='login'?'active':''} onClick={()=>setMode('login')}>Sign in</button><button className={mode==='register'?'active':''} onClick={()=>setMode('register')}>Create account</button></div>
    <form onSubmit={submit} className="form">
      {mode==='register' && <label>Your name<input name="name" value={form.name} onChange={change} required placeholder="Alex Student"/></label>}
      <label>Email address<input name="email" type="email" value={form.email} onChange={change} required placeholder="you@example.com"/></label>
      <label>Password<input name="password" type="password" value={form.password} onChange={change} minLength="6" required placeholder="At least 6 characters"/></label>
      {error && <div className="error">{error}</div>}
      <button className="primary full" disabled={busy}>{busy?'Please wait...':mode==='login'?'Sign in':'Create account'} <Sparkles size={16}/></button>
    </form><p className="tiny muted">Your account and documents are private to your login.</p>
  </section></main>;
}
