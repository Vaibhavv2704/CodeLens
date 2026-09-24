import { Download, CheckCircle2, FileCode2, AlertTriangle } from 'lucide-react';
import { useState } from 'react';
import type { Report } from '../types/agent';

export function ReportView({report}: {report: Report}) {
  const [filter, setFilter] = useState('all');
  const issues = report.issues.filter(i => filter === 'all' || i.severity === filter);
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
    const link = document.createElement('a'); link.href = url; link.download = 'code-review.json'; link.click(); URL.revokeObjectURL(url);
  }
  return <section className="report-section">
    <div className="section-heading"><div><span className="eyebrow">EVIDENCE, THEN ADVICE</span><h2>Review findings</h2></div><button className="secondary" onClick={download}><Download size={15}/> Export JSON</button></div>
    <div className="metrics">{['critical','high','medium','low'].map(s => <button key={s} className={`metric ${filter===s?'selected':''}`} onClick={()=>setFilter(filter===s?'all':s)} aria-pressed={filter===s}><span><i className={`dot ${s}`}/>{s}</span><strong>{report.summary?.[s] ?? 0}</strong></button>)}</div>
    <div className="report-meta"><span>{report.repository.languages?.join(', ') || 'Language not detected'}</span><span>{report.repository.file_count ?? '—'} files inspected</span><span>{report.review.duration_seconds ?? '—'}s elapsed</span><span>Tests: {report.tests?.status ?? 'unavailable'}</span><span>{report.execution?.tool_calls ?? 0} tool calls</span><span>{report.execution?.tool_failures ?? 0} failed attempts</span><span>{report.execution?.recoveries ?? 0} recoveries</span></div>
    {!issues.length && <div className="empty"><CheckCircle2 size={26}/><h3>{report.review.status === 'failed' ? 'Review could not finish' : 'No findings in this view'}</h3><p>Check analysis coverage and limitations below. This is not a guarantee of defect-free code.</p></div>}
    {issues.map((issue, index) => <article className="issue" key={`${issue.file}:${issue.line}:${issue.title}`}>
      <div className="issue-top"><span className={`badge ${issue.severity}`}>{issue.severity}</span><span className="muted">{issue.category}</span><span className="verification">{issue.verification === 'verified' ? <CheckCircle2 size={13}/> : <AlertTriangle size={13}/>} {issue.verification === 'verified' ? 'Verified by tool' : 'Potential finding'}</span></div>
      <h3>{issue.title}</h3><div className="file"><FileCode2 size={14}/>{issue.file}:{issue.line}<span>{Math.round(issue.confidence*100)}% confidence</span></div>
      <pre><code>{issue.evidence}</code></pre><p>{issue.description}</p><div className="fix"><strong>Suggested fix</strong><p>{issue.suggested_fix}</p></div>
      {report.repository.ai_explanations?.filter(e=>e.issue_index === report.issues.indexOf(issue)).map(e=><div className="fix ai" key={index}><strong>AI analysis · advisory</strong><p>{e.explanation}</p><p>{e.suggested_fix}</p></div>)}
    </article>)}
    <div className="limitations"><h3><AlertTriangle size={16}/> Coverage & limitations</h3><p>Python AST rules and conservative JavaScript patterns cover a limited set of issues. Source text remains untrusted.</p><ul>{report.limitations.map((l,i)=><li key={i}>{l}</li>)}</ul></div>
  </section>;
}
