import React from 'react';
import { FileText, Check, ArrowRight, ShieldCheck } from 'lucide-react';

export default function ResolutionTracePanel({ 
  steps, 
  status, 
  winningScore, 
  widthPercentage 
}) {
  // Calculate completed count
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const progressHeightPercentage = (completedCount / steps.length) * 100;

  return (
    <div className="panel-card" style={{ width: `${widthPercentage}%` }}>
      <div className="panel-header">
        <div className="panel-title-group">
          <div className="panel-icon-wrap">
            <FileText size={24} color="#1e293b" />
          </div>
          <h2 className="panel-title">Resolution Trace</h2>
        </div>
      </div>

      {/* Vertical Stepper Timeline */}
      <div className="trace-timeline">
        <div className="timeline-line" />
        <div 
          className="timeline-line-progress" 
          style={{ height: `${Math.min(progressHeightPercentage, 85)}%` }} 
        />

        {steps.map((step, idx) => {
          const isDone = step.status === 'completed';
          const isFirstStep = idx === 0;
          return (
            <div key={step.id} className="timeline-item">
              <div className="timeline-node-wrap">
                <div 
                  className={`timeline-circle ${
                    isDone 
                      ? isFirstStep 
                        ? 'completed-purple' 
                        : 'completed-green' 
                      : 'active-step'
                  }`}
                >
                  {isDone ? <Check size={20} strokeWidth={3} /> : null}
                </div>
                <span className="timeline-label">{step.name}</span>
              </div>
              <span className="timeline-time">{step.timestamp}</span>
            </div>
          );
        })}
      </div>

      {/* Status Transition Pill */}
      <div className="status-pill-box">
        <span className="status-badge-pending">PENDING</span>
        <ArrowRight size={18} className="status-arrow" />
        <span className={`status-badge-processed ${status === 'PROCESSED' ? 'active-badge' : ''}`}>
          {status}
        </span>
      </div>

      {/* Quality Score Card */}
      <div className="score-card">
        <div className="score-left">
          <div className="shield-icon-box">
            <ShieldCheck size={30} strokeWidth={2.5} />
          </div>
          <div className="score-number">
            {winningScore}/100
          </div>
        </div>

        <div className="score-bars">
          <div className="bar-line full" />
          <div className="bar-line med" />
          <div className="bar-line short" />
        </div>
      </div>
    </div>
  );
}
