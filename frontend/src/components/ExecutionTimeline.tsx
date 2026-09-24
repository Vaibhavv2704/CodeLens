import { Activity, Check, Circle, AlertTriangle, LoaderCircle } from 'lucide-react';
import type { AgentEvent, Plan, Step } from '../types/agent';

export function derivePlan(events: AgentEvent[]): Plan | undefined {
  let plan: Plan | undefined;
  for (const e of events) {
    if (e.type === 'plan_created' || e.type === 'plan_updated') plan = structuredClone(e.data) as unknown as Plan;
    if ((e.type === 'step_started' || e.type === 'step_completed') && plan) {
      const step = e.data as unknown as Step;
      plan.steps = plan.steps.map(s => s.id === step.id ? step : s);
    }
  }
  return plan;
}
export function ExecutionTimeline({events, status}: {events: AgentEvent[]; status: string}) {
  const plan = derivePlan(events);
  const visible = events.filter(e => ['tool_started','tool_completed','tool_failed','recovery_started','review_failed'].includes(e.type));
  return <div className="execution-grid"><section className="panel"><div className="panel-heading"><Activity size={17}/><h2>Agent execution</h2><span className={`status ${status}`}>{status}</span></div>
    {plan ? <><p className="strategy">{plan.strategy}</p><ol className="plan">{plan.steps.map(step=><li key={step.id} className={step.status}><span className="step-icon">{step.status === 'completed' ? <Check size={14}/> : step.status === 'running' ? <LoaderCircle size={14} className="spin"/> : step.status === 'degraded' || step.status === 'failed' ? <AlertTriangle size={14}/> : <Circle size={12}/>}</span><div><small>STEP {String(step.id).padStart(2,'0')} · {step.action.replaceAll('_',' ')}</small><p>{step.description}</p></div></li>)}</ol></> : <div className="empty"><LoaderCircle className="spin"/><p>Waiting for the planner…</p></div>}
    </section><section className="panel"><div className="panel-heading"><span className="live-dot"/><h2>Tool activity</h2><span className="count">{visible.length} events</span></div><div className="activity-log" role="log" aria-label="Agent tool activity">{visible.map(e=><div className={`event ${e.type}`} key={e.id}><div className="event-header"><span>{String(e.data.tool || 'agent').replaceAll('_',' ')}</span><time>{new Date(e.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}</time></div><p>{String(e.data.observation || e.data.error || e.data.action || '')}</p>{e.type==='tool_failed'&&<span className="badge high">{String(e.data.category)}</span>}</div>)}{!visible.length&&<p className="strategy">Tool calls and recovery actions will appear here.</p>}</div></section></div>;
}
