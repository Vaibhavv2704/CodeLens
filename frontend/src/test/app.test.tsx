import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { derivePlan } from '../components/ExecutionTimeline';
import { ReportView } from '../components/ReportView';
import type { AgentEvent, Report } from '../types/agent';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
describe('dashboard',()=>{
  it('accepts a repository and an objective',()=>{render(<App/>);expect(screen.getByRole('button',{name:'Start review'})).toBeDisabled();fireEvent.change(screen.getByLabelText(/GitHub repository URL/),{target:{value:'https://github.com/a/b'}});expect(screen.getByRole('button',{name:'Start review'})).toBeEnabled();expect(screen.getByLabelText(/Review objective/)).toBeInTheDocument();});
  it('shows an API failure',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:429,json:async()=>({detail:'Review queue is full'})}));render(<App/>);fireEvent.change(screen.getByLabelText(/GitHub repository URL/),{target:{value:'https://github.com/a/b'}});fireEvent.click(screen.getByRole('button',{name:'Start review'}));expect(await screen.findByRole('alert')).toHaveTextContent('Review queue is full');});
  it('updates plans from persisted events',()=>{const events: AgentEvent[]=[{id:1,type:'plan_created',created_at:'2026-09-25T00:00:00Z',data:{steps:[{id:1,status:'pending'}]}},{id:2,type:'step_completed',created_at:'2026-09-25T00:00:01Z',data:{id:1,status:'completed'}}];expect(derivePlan(events)?.steps[0].status).toBe('completed');});
  it('renders provenance and limitations',()=>{const report={repository:{},review:{status:'completed'},issues:[],limitations:['Docker execution disabled'],summary:{}} as Report;render(<ReportView report={report}/>);expect(screen.getByText('Docker execution disabled')).toBeInTheDocument();expect(screen.getByText(/not a guarantee/)).toBeInTheDocument();});
});
