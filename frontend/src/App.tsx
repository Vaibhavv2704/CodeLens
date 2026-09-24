import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, Braces, ChevronRight, Clock3, Code2, Command, GitBranch, Github, History, Layers3, LockKeyhole, Plus, ShieldCheck, Sparkles, Terminal, X } from 'lucide-react';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { ReportView } from './components/ReportView';
import { getReview, request, setToken, streamEvents } from './services/api';
import type { AgentEvent, Review } from './types/agent';

export default function App() {
  const initialId = new URLSearchParams(location.search).get('review');
  const [page, setPage] = useState<'home'|'review'|'history'>(initialId ? 'review' : 'home');
  const [id, setId] = useState<string|null>(initialId);
  const [url, setUrl] = useState('');
  const [objective, setObjective] = useState('Find important code quality, reliability and maintainability issues.');
  const [review, setReview] = useState<Review|null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [history, setHistory] = useState<Review[]>([]);
  const [error, setError] = useState('');
  const [connection, setConnection] = useState('');
  const [busy, setBusy] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [tokenValue, setTokenValue] = useState('');
  const lastEvent = useRef(0);

  useEffect(()=>{
    if (page === 'history') request<Review[]>('/reviews').then(setHistory).catch(e=>setError(e.message));
  },[page]);

  useEffect(()=>{
    if (!id || page !== 'review') return;
    const controller = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    setReview(null); setEvents([]); lastEvent.current = 0;
    const receive = (event: AgentEvent) => {
      lastEvent.current = Math.max(lastEvent.current, event.id);
      setEvents(current => current.some(e=>e.id===event.id) ? current : [...current,event].sort((a,b)=>a.id-b.id));
    };
    async function connect() {
      try {
        const data = await getReview(id!);
        if (controller.signal.aborted) return;
        setReview(data); data.events?.forEach(receive);
        if (['completed','failed'].includes(data.status)) {setConnection('Saved execution'); return;}
        setConnection('Live connection');
        await streamEvents(id!, lastEvent.current, controller.signal, receive);
        if (controller.signal.aborted) return;
        const finished = await getReview(id!);
        if (controller.signal.aborted) return;
        setReview(finished);
        if (!['completed','failed'].includes(finished.status)) timer=setTimeout(connect,1500);
        else setConnection('Execution complete');
      } catch(e) {
        if (!controller.signal.aborted) { setConnection(`Reconnecting: ${(e as Error).message}`); timer=setTimeout(connect,2500); }
      }
    }
    void connect();
    return ()=>{controller.abort();clearTimeout(timer);};
  },[id,page]);

  function navigate(next: 'home'|'history') { setPage(next); setError(''); window.history.replaceState({},'',location.pathname); }
  function openReview(identifier: string) {setReview(null);setEvents([]);setConnection('Connecting…');lastEvent.current=0;setId(identifier);setPage('review');setError('');window.history.replaceState({},'',`?review=${encodeURIComponent(identifier)}`);}
  async function start(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { const result=await request<{id:string}>('/reviews',{method:'POST',body:JSON.stringify({repository_url:url,objective:objective.trim() || 'Find important code quality, reliability and maintainability issues.'})}); openReview(result.id); }
    catch(e){setError((e as Error).message);} finally{setBusy(false);}
  }
  return <div className="app-shell"><aside className="sidebar"><button className="brand" onClick={()=>navigate('home')}><span className="brand-icon"><Code2 size={22}/></span>codelens<span className="brand-period">.</span></button><div className="workspace-label">WORKSPACE</div><nav><button className={page!=='history'?'active':''} onClick={()=>navigate('home')}><Layers3 size={17}/> Repository reviews <span className="nav-key">R</span></button><button className={page==='history'?'active':''} onClick={()=>navigate('history')}><History size={17}/> Review history</button></nav><div className="sidebar-bottom"><div className="security-note"><ShieldCheck size={20}/><strong>Safe by design</strong><p>Static analysis first.<br/>Isolated execution only.</p></div><button className="settings-button" onClick={()=>setShowSettings(!showSettings)}><span className="avatar">D</span><div>Developer workspace<small>Local & self-hosted</small></div><Command size={15}/></button></div></aside>
    <div className="main-shell"><header className="topbar"><div><span>Workspace</span><ChevronRight size={14}/><strong>{page==='home'?'New review':page==='history'?'Review history':'Repository review'}</strong></div><button className="version" aria-label="API connection settings" onClick={()=>setShowSettings(!showSettings)}>AGENT / v1.0 · CONNECT</button></header><main>
      {showSettings&&<section className="settings panel"><div className="section-heading"><h3>API connection</h3><button aria-label="Close settings" onClick={()=>setShowSettings(false)}><X size={18}/></button></div><label htmlFor="token">API bearer token (optional, held in memory only)</label><input id="token" type="password" value={tokenValue} onChange={e=>setTokenValue(e.target.value)}/><button className="primary" onClick={()=>{setToken(tokenValue);setShowSettings(false);setError('');}}>Apply token</button></section>}
      {error&&<div role="alert" className="error-banner">{error}<button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
      {page==='home'&&<><div className="page-title"><span className="eyebrow"><span className="live-dot"/> AUTONOMOUS CODE INTELLIGENCE</span><h1>A second set of eyes.<br/><span>For your entire repository.</span></h1><p>AI-powered multi-tool repository analysis with autonomous<br className="desktop-br"/> planning, evidence-backed findings, and failure recovery.</p></div>
      <section className="review-form panel"><div className="panel-heading"><Github size={20}/><div><h2>Start a repository review</h2><p>Give the agent a repository and a goal. It handles the next steps.</p></div><span className="tag">GITHUB</span></div><form onSubmit={start}><label htmlFor="repo">GitHub repository URL <span className="required">*</span></label><div className="input-icon"><GitBranch size={17}/><input id="repo" type="url" required placeholder="https://github.com/owner/repository" value={url} onChange={e=>setUrl(e.target.value)} autoComplete="off"/></div><div className="input-hint">Public repositories work without a token. Private access requires backend credentials.</div><label htmlFor="objective">Review objective <span className="optional">OPTIONAL</span></label><textarea id="objective" rows={3} maxLength={1500} minLength={3} value={objective} onChange={e=>setObjective(e.target.value)} placeholder="What should the agent focus on?"/><div className="form-footer"><span><LockKeyhole size={14}/> Your repository is never modified</span><button className="primary" disabled={busy || !url} type="submit">{busy?'Creating review…':'Start review'}<ArrowRight size={17}/></button></div></form></section>
      <div className="try-example"><span>Need a starting point?</span><button onClick={()=>setUrl('https://github.com/pallets/itsdangerous')}>pallets / itsdangerous <ArrowUpRight size={13}/></button></div>
      <section className="how-section"><div className="section-heading"><h2>From repository to actionable insight</h2><span>ONE GOAL. SEVEN STEPS.</span></div><div className="feature-grid"><article><span className="feature-icon"><GitBranch size={20}/></span><span className="feature-number">01</span><h3>Inspect & plan</h3><p>The agent maps your repository and selects a language-aware analysis plan.</p></article><article><span className="feature-icon"><Terminal size={20}/></span><span className="feature-number">02</span><h3>Analyze & recover</h3><p>Watch tool calls unfold live, with bounded retries and safe fallbacks.</p></article><article><span className="feature-icon"><Braces size={20}/></span><span className="feature-number">03</span><h3>Verify & report</h3><p>Get source-linked findings, practical fixes, and an exportable JSON report.</p></article></div></section><div className="bottom-note"><Sparkles size={14}/><span>Autonomous GitHub Code Review Agent</span><span className="separator">/</span><span>Built for transparent, inspectable reviews</span></div></>}
      {page==='review'&&<><div className="section-heading review-title"><div><span className="eyebrow">REPOSITORY REVIEW</span><h1>{review?.repository_url.replace('https://github.com/','') || 'Preparing review…'}</h1><p>{review?.objective}</p></div><button className="secondary" onClick={()=>navigate('home')}><Plus size={16}/> New review</button></div><div className="connection"><span className="live-dot"/>{connection || 'Connecting…'}</div><ExecutionTimeline events={events} status={review?.status || 'queued'}/>{review?.report&&<ReportView report={review.report}/>}</>}
      {page==='history'&&<><div className="section-heading review-title"><div><span className="eyebrow">YOUR WORKSPACE</span><h1>Review history</h1><p>Revisit findings and the full execution trail.</p></div><button className="primary" onClick={()=>navigate('home')}><Plus size={16}/> New review</button></div><section className="panel history">{history.length?history.map(r=><button className="history-row" key={r.id} onClick={()=>openReview(r.id)}><Github size={21}/><div><h3>{r.repository_url.replace('https://github.com/','')}</h3><p>{r.objective}</p><small><Clock3 size={12}/>{new Date(r.created_at).toLocaleString()}</small></div><span className={`status ${r.status}`}>{r.status}</span><ArrowUpRight size={17}/></button>):<div className="empty"><History size={28}/><h3>No reviews yet</h3><p>Your completed and in-progress reviews will appear here.</p></div>}</section></>}
    </main><footer><span><ShieldCheck size={13}/> Observable by design</span><span>Plan → Act → Validate → Recover → Report</span></footer></div></div>;
}
