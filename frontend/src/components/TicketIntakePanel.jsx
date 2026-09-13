import React, { useState } from 'react';
import { Ticket, Plus, Send } from 'lucide-react';

export default function TicketIntakePanel({ 
  tickets, 
  activeTicketId, 
  onSelectTicket, 
  onAddTicket,
  widthPercentage 
}) {
  const [ticketInput, setTicketInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ticketInput.trim()) return;
    if (onAddTicket) {
      onAddTicket(ticketInput.trim());
    }
    setTicketInput('');
  };

  return (
    <div className="panel-card" style={{ width: `${widthPercentage}%` }}>
      <div className="panel-header">
        <div className="panel-title-group">
          <div className="panel-icon-wrap">
            <Ticket size={24} color="#1e293b" />
          </div>
          <h2 className="panel-title">Ticket Intake</h2>
        </div>
      </div>

      <div className="intake-queue-badge">
        <span className="queue-label">Live Queue</span>
        <span className="queue-count">{tickets.length}</span>
      </div>

      {/* TICKET ENTRY INPUT FORM */}
      <form onSubmit={handleSubmit} className="intake-input-container">
        <input 
          type="text"
          className="intake-text-input"
          placeholder="Enter ticket text or issue description..."
          value={ticketInput}
          onChange={(e) => setTicketInput(e.target.value)}
        />
        <button type="submit" className="intake-submit-btn" title="Submit Ticket to Queue">
          <Send size={16} />
        </button>
      </form>

      <div className="ticket-list">
        {tickets.map((ticket) => {
          const isActive = ticket.id === activeTicketId;
          const displayId = ticket.id.toUpperCase();
          const categoryTag = ticket.category ? ticket.category.toUpperCase() : 'TICKET';
          const isRebid = ticket.is_rebid || ticket.id.includes('REBID');

          return (
            <div 
              key={ticket.id}
              className={`ticket-card ${isActive ? 'active' : ''} ${isRebid ? 'rebid-ticket' : ''}`}
              onClick={() => onSelectTicket(ticket.id)}
            >
              <div className="ticket-left">
                <div className="ticket-icon">
                  <Ticket size={20} />
                </div>
                <span 
                  className="ticket-dot" 
                  style={{ backgroundColor: ticket.dotColor || '#635bff' }} 
                />
                <div className="ticket-id-wrapper">
                  <span className="ticket-id-display">{displayId}</span>
                  {ticket.title && ticket.title !== ticket.id && (
                    <span className="ticket-subtext">{ticket.title}</span>
                  )}
                </div>
              </div>
              <div className="ticket-meta-right">
                {isRebid ? (
                  <span className="rebid-badge">RE-BID</span>
                ) : ticket.timeAgo === 'Completed' || ticket.executedResult ? (
                  <span className="status-badge badge-completed" style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: 600 }}>COMPLETED</span>
                ) : (
                  <span className="status-badge badge-queued" style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99, 91, 255, 0.15)', color: '#635bff', fontWeight: 600 }}>QUEUED</span>
                )}
                <span className="ticket-time">{ticket.timeAgo || 'Just now'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
