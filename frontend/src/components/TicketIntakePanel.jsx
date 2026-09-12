import React from 'react';
import { Ticket } from 'lucide-react';

export default function TicketIntakePanel({ 
  tickets, 
  activeTicketId, 
  onSelectTicket, 
  widthPercentage 
}) {
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
        <span className="queue-count">{tickets.length + 7}</span>
      </div>

      <div className="ticket-list">
        {tickets.map((ticket) => {
          const isActive = ticket.id === activeTicketId;
          return (
            <div 
              key={ticket.id}
              className={`ticket-card ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTicket(ticket.id)}
            >
              <div className="ticket-left">
                <div className="ticket-icon">
                  <Ticket size={20} />
                </div>
                <span 
                  className="ticket-dot" 
                  style={{ backgroundColor: ticket.dotColor }} 
                />
                <span className="ticket-title">{ticket.title}</span>
              </div>
              <span className="ticket-time">{ticket.timeAgo}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
