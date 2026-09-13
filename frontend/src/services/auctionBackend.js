// Auction Backend Simulation & Live FastAPI Integration Engine

export const BACKEND_URL = 'http://localhost:8000';

// Remove static hardcoded tickets as requested
export const INITIAL_TICKETS = [];

export const INITIAL_AGENTS = [
  {
    id: 'agent-1',
    agent_id: 'billing_agent',
    name: 'Billing Agent',
    role: 'Payment & Ledger Specialist',
    avatarColor: 'orange',
    accentColor: '#f97316',
    baseScore: 88,
    slaSpeed: '< 15s',
    accuracy: '98.6%',
    tagline: 'Specialized in transaction reversals, refund verification & ledger balancing.',
    capabilities: ['Refund Processing', 'Invoice Reissue', 'Duplicate Charge Reversal'],
    thought: 'Evaluating transaction ledger... Verifying payment gateway status.'
  },
  {
    id: 'agent-2',
    agent_id: 'technical_agent',
    name: 'Technical Agent',
    role: 'Infrastructure & Account Resolution',
    avatarColor: 'emerald',
    accentColor: '#10b981',
    baseScore: 92,
    slaSpeed: '< 8s',
    accuracy: '99.4%',
    tagline: 'High-precision automated environment repair & dashboard resynchronization.',
    capabilities: ['Account Unlock', 'Session Reset', 'Order Resync', 'Dashboard Restore'],
    thought: 'Analyzing environment health... Identifying session expiration and sync errors.'
  },
  {
    id: 'agent-3',
    agent_id: 'retention_agent',
    name: 'Retention Agent',
    role: 'Customer Retention & Churn Prevention',
    avatarColor: 'blue',
    accentColor: '#3b82f6',
    baseScore: 74,
    slaSpeed: '< 25s',
    accuracy: '97.2%',
    tagline: 'Ensures customer satisfaction, churn reduction and loyalty offers.',
    capabilities: ['Churn Risk Assessment', 'Loyalty Points Offer', 'Subscription Pause'],
    thought: 'Calculating churn probability index... Formulating tailored retention offer.'
  }
];

export const RESOLUTION_STEPS_TEMPLATE = [
  { id: 'step-1', name: 'Investigate', timestamp: '10:14', status: 'pending' },
  { id: 'step-2', name: 'Diagnose', timestamp: '10:15', status: 'pending' },
  { id: 'step-3', name: 'Execute', timestamp: '10:15', status: 'pending' },
  { id: 'step-4', name: 'Vet', timestamp: '10:16', status: 'pending' },
  { id: 'step-5', name: 'Done', timestamp: '10:16', status: 'pending' }
];

/**
 * Calculates dynamic agent bids & thoughts based on ticket text & optional backend execution result
 */
export function calculateAgentBids(ticket, backendResult = null) {
  if (!ticket) return INITIAL_AGENTS;

  let bScore = 75;
  let tScore = 75;
  let rScore = 75;

  let bThought = "Evaluating financial ledger and invoice records...";
  let tThought = "Checking account status, active session, and dashboard health...";
  let rThought = "Assessing customer sentiment, churn probability, and loyalty tiers...";

  const text = (ticket.text || ticket.description || ticket.title || ticket.ticket_text || '').toLowerCase();

  // If real backend result with bids exists, extract actual scores straight from Python orchestrator
  if (backendResult && backendResult.trace_steps && backendResult.trace_steps.length > 0) {
    const lastStep = backendResult.trace_steps[backendResult.trace_steps.length - 1];
    if (lastStep.bids && Array.isArray(lastStep.bids)) {
      for (const b of lastStep.bids) {
        const score = Math.round((b.final_bid || 0.75) * 100);
        if (b.agent_id === 'billing_agent') bScore = score;
        if (b.agent_id === 'technical_agent') tScore = score;
        if (b.agent_id === 'retention_agent') rScore = score;
      }
    }
    if (backendResult.final_statement || backendResult.diagnosis) {
      const winnerId = backendResult.winner;
      const statement = backendResult.final_statement || backendResult.diagnosis;
      if (winnerId === 'billing_agent') bThought = statement;
      else if (winnerId === 'technical_agent') tThought = statement;
      else if (winnerId === 'retention_agent') rThought = statement;
    }
  } else {
    // Dynamic rule-based bid evaluation based on ticket text keywords
    if (text.includes('refund') || text.includes('charge') || text.includes('billing') || text.includes('duplicate') || text.includes('money') || text.includes('invoice')) {
      bScore = Math.floor(Math.random() * 5) + 93; // 93-97
      tScore = Math.floor(Math.random() * 10) + 75;
      rScore = Math.floor(Math.random() * 10) + 70;
      bThought = "High match: Refund anomaly detected in billing sandbox. Reconciling transaction hash.";
    } else if (text.includes('locked') || text.includes('login') || text.includes('dashboard') || text.includes('visible') || text.includes('password') || text.includes('sync')) {
      tScore = Math.floor(Math.random() * 5) + 94; // 94-98
      bScore = Math.floor(Math.random() * 10) + 74;
      rScore = Math.floor(Math.random() * 10) + 72;
      tThought = "High match: Technical environment fault detected. Resynchronizing session & dashboard state.";
    } else if (text.includes('cancel') || text.includes('subscription') || text.includes('patience') || text.includes('issue') || text.includes('leaving')) {
      rScore = Math.floor(Math.random() * 5) + 92; // 92-96
      bScore = Math.floor(Math.random() * 10) + 78;
      tScore = Math.floor(Math.random() * 10) + 76;
      rThought = "High match: High dissatisfaction & churn risk score. Formulating immediate retention offer.";
    } else {
      bScore = Math.floor(Math.random() * 10) + 82;
      tScore = Math.floor(Math.random() * 10) + 85;
      rScore = Math.floor(Math.random() * 10) + 80;
    }
  }

  return [
    { ...INITIAL_AGENTS[0], bidScore: bScore, thought: bThought },
    { ...INITIAL_AGENTS[1], bidScore: tScore, thought: tThought },
    { ...INITIAL_AGENTS[2], bidScore: rScore, thought: rThought }
  ];
}

// -----------------------------------------------------------------------------
// LIVE FASTAPI BACKEND HELPERS
// -----------------------------------------------------------------------------

export async function fetchQueue() {
  try {
    const res = await fetch(`${BACKEND_URL}/queue`);
    if (!res.ok) throw new Error('Failed to fetch queue');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline or unreachable:', err);
    return null;
  }
}

export async function fetchAgentTrace() {
  try {
    const res = await fetch(`${BACKEND_URL}/agent_trace`);
    if (!res.ok) throw new Error('Failed to fetch trace logs');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline or unreachable:', err);
    return null;
  }
}

export async function injectTicketToBackend(ticketText) {
  try {
    const res = await fetch(`${BACKEND_URL}/inject_ticket`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticket_text: ticketText })
    });
    if (!res.ok) throw new Error('Failed to inject ticket');
    return await res.json();
  } catch (err) {
    console.warn('Backend inject failed:', err);
    return null;
  }
}

export async function enqueueTicketToBackend(ticketText, urgencyScore = 50) {
  try {
    const res = await fetch(`${BACKEND_URL}/enqueue_ticket`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticket_text: ticketText, urgency_score: urgencyScore })
    });
    if (!res.ok) throw new Error('Failed to enqueue ticket');
    return await res.json();
  } catch (err) {
    console.warn('Backend enqueue failed:', err);
    return null;
  }
}

export async function executeNextQueueTicket() {
  try {
    const res = await fetch(`${BACKEND_URL}/execute_next`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to execute next ticket');
    return await res.json();
  } catch (err) {
    console.warn('Backend execute_next failed:', err);
    return null;
  }
}

export async function executeEntireQueue() {
  try {
    const res = await fetch(`${BACKEND_URL}/execute_queue`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to execute queue');
    return await res.json();
  } catch (err) {
    console.warn('Backend execute_queue failed:', err);
    return null;
  }
}

export async function resetBackendQueue() {
  try {
    const res = await fetch(`${BACKEND_URL}/reset_queue`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset queue');
    return await res.json();
  } catch (err) {
    console.warn('Backend reset_queue failed:', err);
    return null;
  }
}

/**
 * Injects a ticket AND returns both execution result + full updated trace logs
 * in a single atomic response. Eliminates the race condition where the frontend
 * polls /agent_trace before the trace data from the just-injected ticket is written.
 */
export async function injectAndTrace(ticketText, urgencyScore = 50) {
  try {
    const res = await fetch(`${BACKEND_URL}/inject_and_trace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticket_text: ticketText, urgency_score: urgencyScore })
    });
    if (!res.ok) throw new Error('Failed to inject and trace ticket');
    return await res.json();
  } catch (err) {
    console.warn('Backend inject_and_trace failed:', err);
    return null;
  }
}

/**
 * Fetches pre-built test ticket texts that exercise all three agent types
 * and different collaboration scenarios.
 */
export async function fetchTestTickets() {
  try {
    const res = await fetch(`${BACKEND_URL}/test_tickets`);
    if (!res.ok) throw new Error('Failed to fetch test tickets');
    return await res.json();
  } catch (err) {
    console.warn('Backend test_tickets failed:', err);
    return null;
  }
}
