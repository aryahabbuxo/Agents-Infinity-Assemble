import React, { useState } from 'react';
import { X } from 'lucide-react';

export default function InjectTicketModal({ isOpen, onClose, onInject }) {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('billing');
  const [amount, setAmount] = useState('$120.00');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title) return;

    let dotColor = '#ef4444';
    if (category === 'payment') dotColor = '#f59e0b';
    if (category === 'refund' || category === 'tax') dotColor = '#10b981';

    const newTicket = {
      id: `t-${Date.now()}`,
      title,
      category,
      dotColor,
      timeAgo: 'Just now',
      priority: 'High',
      description: `Custom ticket injected for category: ${category}`,
      amount,
      customer: 'Custom User'
    };

    onInject(newTicket);
    setTitle('');
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Inject Ticket into Queue</h3>
          <button className="btn-pill" onClick={onClose} style={{ padding: 6 }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Ticket Subject / Title</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g. Overcharge dispute on Invoice #9021" 
              value={title} 
              onChange={e => setTitle(e.target.value)} 
              required 
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select 
              className="form-select" 
              value={category} 
              onChange={e => setCategory(e.target.value)}
            >
              <option value="billing">Billing & Duplicate Charge</option>
              <option value="payment">Payment & Credit Card Failure</option>
              <option value="tax">Tax & VAT Compliance</option>
              <option value="refund">Tier Upgrade Refund</option>
              <option value="subscription">Subscription Cancel</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Transaction Amount</label>
            <input 
              type="text" 
              className="form-input" 
              value={amount} 
              onChange={e => setAmount(e.target.value)} 
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
            <button type="button" className="btn-pill" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-pill btn-primary">
              Inject into Live Queue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
