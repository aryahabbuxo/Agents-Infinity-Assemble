import React, { useState } from 'react';
import { 
  Terminal, 
  Play, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  ChevronDown, 
  ChevronRight,
  Layers,
  Zap,
  ListOrdered
} from 'lucide-react';

/**
 * Helper to safely convert any value (strings, numbers, objects, arrays) into a printable string
 * so React never crashes with "Objects are not valid as a React child".
 */
function renderSafeText(val, fallback = '') {
  if (val === null || val === undefined) return fallback;
  if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
    return String(val);
  }
  if (typeof val === 'object') {
    if (val.statement) return renderSafeText(val.statement, fallback);
    if (val.message) return renderSafeText(val.message, fallback);
    if (val.diagnosis) return renderSafeText(val.diagnosis, fallback);
    if (val.text) return renderSafeText(val.text, fallback);
    if (val.clause) return renderSafeText(val.clause, fallback);
    if (val.action) return renderSafeText(val.action, fallback);
    try {
      return JSON.stringify(val);
    } catch (e) {
      return fallback;
    }
  }
  return String(val);
}

/**
 * React Error Boundary component to prevent blank screen crashes
 */
class TraceErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("AgentCallTrace Error Boundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', color: '#ef4444', textAlign: 'center', background: '#1e293b', borderRadius: '12px', margin: '20px' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>⚠️ Agent Call Trace Error Captured</h3>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>A UI rendering error occurred, but the application remains stable.</p>
          <button 
            style={{ padding: '8px 16px', background: '#635bff', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', marginTop: '12px', fontWeight: 600 }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Reload Dashboard View
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function DashboardView({ 
  traceLogs = [], 
  queueData = { pending_queue: [], executed_tickets: [], executed_tickets_summary: [] }, 
  agentBalances = {}, 
  instanceIndexes = {},
  onExecuteNext,
  onExecuteAll,
  onResetQueue,
  onRefreshTrace
}) {
  const [selectedLogIndex, setSelectedLogIndex] = useState(0);
  const [filterAgent, setFilterAgent] = useState('all');
  const [expandedJsonIndex, setExpandedJsonIndex] = useState(null);

  const safeTraceLogs = Array.isArray(traceLogs) ? traceLogs.filter(Boolean) : [];
  const safePendingQueue = Array.isArray(queueData?.pending_queue) ? queueData.pending_queue.filter(Boolean) : [];
  const safeExecutedSummary = Array.isArray(queueData?.executed_tickets_summary) ? queueData.executed_tickets_summary.filter(Boolean) : [];

  const logs = safeTraceLogs.filter(log => {
    if (filterAgent === 'all') return true;
    return log.winner === filterAgent;
  });

  const activeLogIndex = selectedLogIndex < logs.length ? selectedLogIndex : 0;
  const activeLog = logs[activeLogIndex] || logs[0] || null;

  return (
    <div className="trace-dashboard-container">
      {/* TOP CONTROL & METRICS BAR */}
      <div className="trace-top-bar">
        <div className="trace-metrics-group">
          <div className="metric-chip">
            <Terminal size={18} color="#635bff" />
            <div>
              <span className="metric-value">{safeTraceLogs.length}</span>
              <span className="metric-label">Agent Calls</span>
            </div>
          </div>

          <div className="metric-chip">
            <ListOrdered size={18} color="#f59e0b" />
            <div>
              <span className="metric-value">{safePendingQueue.length}</span>
              <span className="metric-label">Queued Tickets</span>
            </div>
          </div>

          <div className="metric-chip">
            <CheckCircle2 size={18} color="#10b981" />
            <div>
              <span className="metric-value">{safeExecutedSummary.length}</span>
              <span className="metric-label">Executed Tickets</span>
            </div>
          </div>
        </div>

        <div className="trace-actions-group">
          <button 
            className="btn-pill btn-primary"
            onClick={onExecuteNext}
            title="Pop & Execute Next Ticket in Queue"
          >
            <Play size={16} />
            <span>Execute Next Ticket</span>
          </button>

          <button 
            className="btn-pill"
            onClick={onExecuteAll}
            title="Execute Entire Ticket Queue"
          >
            <Zap size={16} color="#f59e0b" />
            <span>Execute Queue</span>
          </button>

          <button 
            className="btn-pill"
            onClick={onRefreshTrace}
            title="Fetch Latest Trace Logs"
          >
            <RefreshCw size={16} />
            <span>Refresh Logs</span>
          </button>

          <button 
            className="btn-pill"
            onClick={onResetQueue}
            title="Reset Ticket Queue"
          >
            <span>Reset Queue</span>
          </button>
        </div>
      </div>

      {/* MAIN 3-PANEL GRID LAYOUT */}
      <div className="trace-grid">
        {/* PANEL 1: TICKET QUEUE & RE-BID PIPELINE */}
        <div className="trace-panel panel-queue">
          <div className="trace-panel-header">
            <Layers size={18} color="#6496e8" />
            <h3>Ticket Queue & Re-Bids</h3>
          </div>

          <div className="queue-section-title">Pending Queue ({safePendingQueue.length})</div>
          <div className="queue-scroll-list">
            {safePendingQueue.length > 0 ? (
              safePendingQueue.map((t, i) => (
                <div key={t.ticket_id || i} className={`queue-item-card ${t.is_rebid ? 'is-rebid' : ''}`}>
                  <div className="queue-item-header">
                    <span className="queue-item-id">{renderSafeText(t.ticket_id, `T-QUEUED-${i+1}`)}</span>
                    <span className={`status-badge ${t.is_rebid ? 'badge-rebid' : 'badge-queued'}`}>
                      {t.is_rebid ? 'RE-BID QUEUED' : 'QUEUED'}
                    </span>
                  </div>
                  <div className="queue-item-text">{renderSafeText(t.text || t.ticket_text || t.title, 'No text')}</div>
                  <div className="queue-item-footer">
                    <span>Order: {renderSafeText(t.order_id, 'N/A')}</span>
                    <span>Urgency: {t.urgency_score || 50}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">Queue is empty. Submit a ticket in Ticket Intake!</div>
            )}
          </div>

          <div className="queue-section-title">Executed Tickets ({safeExecutedSummary.length})</div>
          <div className="queue-scroll-list executed-list">
            {safeExecutedSummary.map((item, i) => (
              <div key={item.ticket_id || i} className="queue-item-card executed">
                <div className="queue-item-header">
                  <span className="queue-item-id">{renderSafeText(item.ticket_id, `T-EXEC-${i+1}`)}</span>
                  <span className="status-badge badge-completed">COMPLETED</span>
                </div>
                {item.ticket_text && (
                  <div className="queue-item-text">{renderSafeText(item.ticket_text)}</div>
                )}
                <div className="queue-item-sub">Winner: <strong>{renderSafeText(item.winner, 'Market Agent')}</strong></div>
                {item.final_statement && (
                  <div className="queue-item-statement">"{renderSafeText(item.final_statement)}"</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* PANEL 2: STEP-BY-STEP AGENT CALL TRACE & TERMINAL */}
        <div className="trace-panel panel-calls">
          <div className="trace-panel-header">
            <Terminal size={18} color="#10b981" />
            <h3>Agent Execution Calls</h3>
            <div className="filter-select-wrap">
              <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
                <option value="all">All Agents</option>
                <option value="billing_agent">Billing Agent</option>
                <option value="technical_agent">Technical Agent</option>
                <option value="retention_agent">Retention Agent</option>
              </select>
            </div>
          </div>

          <div className="calls-split-view">
            {/* CALL SELECTOR LIST */}
            <div className="calls-list-sidebar">
              {logs.length > 0 ? (
                logs.map((log, idx) => {
                  const isSelected = activeLogIndex === idx;
                  const isRebid = log.is_rebid || log.rebound_triggered;
                  return (
                    <div 
                      key={idx} 
                      className={`call-summary-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => setSelectedLogIndex(idx)}
                    >
                      <div className="call-card-top">
                        <span className="call-time">{renderSafeText(log.timestamp, 'Step ' + (idx + 1))}</span>
                        <span className="call-ticket-badge">{renderSafeText(log.ticket_id, 'T-USER')}</span>
                      </div>
                      <div className="call-winner-line">
                        Winner: <span className="winner-highlight">{renderSafeText(log.winner, 'Agent')}</span>
                      </div>
                      {isRebid && <span className="call-rebid-tag">RE-BID ITERATION {log.iteration || 2}</span>}
                    </div>
                  );
                })
              ) : (
                <div className="empty-state">No agent calls recorded yet. Execute tickets from the queue.</div>
              )}
            </div>

            {/* DETAILED LOG INSPECTOR */}
            <div className="calls-detail-view">
              {activeLog ? (
                <div className="log-detail-content">
                  {/* STAGE 1: BIDS */}
                  <div className="detail-section">
                    <h4 className="stage-title">STAGE 1: Market Bidding Breakdown (Iteration {activeLog.iteration || 1})</h4>
                    <div className="table-responsive">
                      <table className="bids-table">
                        <thead>
                          <tr>
                            <th>Agent</th>
                            <th>Raw Confidence</th>
                            <th>Load Penalty</th>
                            <th>Urgency Weight</th>
                            <th>Final Bid</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Array.isArray(activeLog.bids) && activeLog.bids.filter(Boolean).map((b, i) => {
                            const isWinner = b.agent_id === activeLog.winner;
                            return (
                              <tr key={i} className={isWinner ? 'row-winner' : ''}>
                                <td>{renderSafeText(b.agent_id, 'agent')}</td>
                                <td>{Number(b.raw_confidence || 0).toFixed(3)}</td>
                                <td>{Number(b.load_penalty || 0).toFixed(3)}</td>
                                <td>{Number(b.urgency_weight || 0).toFixed(3)}</td>
                                <td><strong>{Number(b.final_bid || 0).toFixed(3)}</strong></td>
                                <td>{isWinner ? <span className="winner-pill">WINNER</span> : 'Bid'}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* STAGE 2: DIAGNOSIS */}
                  <div className="detail-section">
                    <h4 className="stage-title">STAGE 2: Lead Agent Diagnosis & Resolution</h4>
                    <div className="diagnosis-box">
                      <div className="diag-label">Lead Agent: <span>{renderSafeText(activeLog.winner, 'Lead Agent')}</span></div>
                      <div className="diag-text">{renderSafeText(activeLog.diagnosis, 'Diagnosis completed.')}</div>
                    </div>
                  </div>

                  {/* STAGE 3: NEGOTIATION */}
                  {Array.isArray(activeLog.negotiation_transcript) && activeLog.negotiation_transcript.length > 0 && (
                    <div className="detail-section">
                      <h4 className="stage-title">STAGE 3: P2P Structured Negotiation Transcript</h4>
                      <div className="transcript-list">
                        {activeLog.negotiation_transcript.filter(Boolean).map((msg, i) => (
                          <div key={i} className="transcript-msg">
                            <span className="msg-route">[{renderSafeText(msg.sender, 'agent')}] &rarr; [{renderSafeText(msg.receiver, 'all')}]</span>
                            <span className="msg-action">{renderSafeText(msg.action || msg.message_type, 'negotiate')}</span>
                            {(msg.my_assigned_subtask || msg.subtask) && (
                              <div className="msg-detail">Subtask: {renderSafeText(msg.my_assigned_subtask || msg.subtask)}</div>
                            )}
                            {msg.rationale && (
                              <div className="msg-detail rationale">Rationale: {renderSafeText(msg.rationale)}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* STAGE 4: SANDBOX EXECUTION */}
                  <div className="detail-section">
                    <h4 className="stage-title">STAGE 4: Sandbox State Diffs & Actions</h4>
                    {Array.isArray(activeLog.state_before_after) && activeLog.state_before_after.length > 0 ? (
                      <div className="diff-list">
                        {activeLog.state_before_after.filter(Boolean).map((diff, i) => (
                          <div key={i} className="diff-card">
                            <div className="diff-action">Action: {renderSafeText(diff.action, 'State Change')}</div>
                            <div className="diff-before">Before: {JSON.stringify(diff.before ?? {})}</div>
                            <div className="diff-after">After: {JSON.stringify(diff.after ?? {})}</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="executed-actions-text">
                        Actions Executed: {JSON.stringify(activeLog.execution_results || [])}
                      </div>
                    )}
                  </div>

                  {/* STAGE 5: VETTING */}
                  {activeLog.vetting && (
                    <div className="detail-section">
                      <h4 className="stage-title">
                        STAGE 5: Requirement Coverage Vetting & Checklist
                        <span className={`cov-score-pill ${Number(activeLog.vetting.coverage_score || 0) >= 0.7 ? 'pass' : 'fail'}`}>
                          Score: {(Number(activeLog.vetting.coverage_score || 0) * 100).toFixed(1)}%
                        </span>
                      </h4>
                      <div className="checklist-container">
                        {Array.isArray(activeLog.vetting.clause_checklist) && activeLog.vetting.clause_checklist.filter(Boolean).map((chk, i) => (
                          <div key={i} className={`checklist-item ${chk.addressed ? 'addressed' : 'unaddressed'}`}>
                            {chk.addressed ? (
                              <CheckCircle2 size={16} color="#10b981" />
                            ) : (
                              <AlertTriangle size={16} color="#ef4444" />
                            )}
                            <span className="clause-text">"{renderSafeText(chk.clause)}"</span>
                            {Array.isArray(chk.matched_keywords) && chk.matched_keywords.length > 0 && (
                              <span className="matched-tags">Matched: {chk.matched_keywords.map(k => renderSafeText(k)).join(', ')}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* STAGE 6: CALIBRATION PENALTY */}
                  {activeLog.penalty_info && (
                    <div className="detail-section">
                      <h4 className="stage-title">STAGE 6: Calibration Gap Penalty Engine</h4>
                      <div className="penalty-summary-grid">
                        <div className="penalty-card">
                          <span>Raw Confidence</span>
                          <strong>{Number(activeLog.penalty_info.raw_confidence || 0).toFixed(3)}</strong>
                        </div>
                        <div className="penalty-card">
                          <span>Actual Coverage</span>
                          <strong>{Number(activeLog.penalty_info.coverage_score || 0).toFixed(3)}</strong>
                        </div>
                        <div className="penalty-card">
                          <span>Calibration Gap</span>
                          <strong className={Number(activeLog.penalty_info.calibration_gap || 0) > 0 ? 'gap-over' : 'gap-ok'}>
                            {Number(activeLog.penalty_info.calibration_gap || 0).toFixed(3)}
                          </strong>
                        </div>
                        <div className="penalty-card">
                          <span>Penalty Amount</span>
                          <strong className={Number(activeLog.penalty_info.penalty || 0) > 0 ? 'text-red' : 'text-green'}>
                            -${Number(activeLog.penalty_info.penalty || 0).toFixed(2)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* RAW JSON OUTPUT ACCORDION */}
                  <div className="detail-section">
                    <button 
                      className="json-toggle-btn"
                      onClick={() => setExpandedJsonIndex(expandedJsonIndex === activeLogIndex ? null : activeLogIndex)}
                    >
                      {expandedJsonIndex === activeLogIndex ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      <span>View Terminal JSON Output</span>
                    </button>
                    {expandedJsonIndex === activeLogIndex && (
                      <pre className="json-terminal-code">
                        {JSON.stringify(activeLog, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ) : (
                <div className="empty-state">Select an execution step from the left column to inspect calls.</div>
              )}
            </div>
          </div>
        </div>

        {/* PANEL 3: AGENT PERFORMANCE & INSTANCE INDEX */}
        <div className="trace-panel panel-agents">
          <div className="trace-panel-header">
            <Cpu size={18} color="#f59e0b" />
            <h3>Agent Performance & Instance Index</h3>
          </div>

          <div className="agents-index-scroll">
            {['billing_agent', 'technical_agent', 'retention_agent'].map(agentId => {
              const balance = Number(agentBalances?.[agentId] || 0);
              const instances = Array.isArray(instanceIndexes?.[agentId]) ? instanceIndexes[agentId] : [];

              return (
                <div key={agentId} className="agent-index-card">
                  <div className="agent-card-header">
                    <span className="agent-id-title">{agentId.replace('_', ' ').toUpperCase()}</span>
                    <span className="agent-balance-badge">${balance.toFixed(2)}</span>
                  </div>

                  <div className="instance-index-table-wrap">
                    <div className="table-caption">Instance Index Rankings (Top &rarr; Bottom):</div>
                    {instances.length > 0 ? (
                      <table className="instance-table">
                        <thead>
                          <tr>
                            <th>Rank</th>
                            <th>Ticket</th>
                            <th>Coverage</th>
                            <th>Gap</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {instances.filter(Boolean).map((inst, i) => {
                            const cov = Number(inst?.coverage_score || 0);
                            const gapVal = Number(inst?.gap || 0);
                            return (
                              <tr key={i} className={i === 0 ? 'row-top' : ''}>
                                <td>{i === 0 ? 'TOP' : i === instances.length - 1 ? 'BOT' : `#${i + 1}`}</td>
                                <td>{renderSafeText(inst?.ticket_id, 'T000')}</td>
                                <td>{cov.toFixed(2)}</td>
                                <td className={gapVal > 0 ? 'text-red' : 'text-green'}>
                                  {gapVal > 0 ? `+${gapVal.toFixed(2)}` : gapVal.toFixed(2)}
                                </td>
                                <td>
                                  <span className={`mini-status ${inst?.success ? 'pass' : 'fail'}`}>
                                    {inst?.success ? 'PASS' : 'FAIL'}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    ) : (
                      <div className="no-instances">No past ticket instances indexed yet.</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentCallTraceDashboard(props) {
  return (
    <TraceErrorBoundary>
      <DashboardView {...props} />
    </TraceErrorBoundary>
  );
}
