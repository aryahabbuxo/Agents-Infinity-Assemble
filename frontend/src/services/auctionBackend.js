// Auction Backend Simulation Engine

export const INITIAL_TICKETS = [
  {
    id: 't-101',
    title: 'Duplicate charge',
    category: 'billing',
    dotColor: '#ef4444', // Red
    timeAgo: '8s',
    priority: 'High',
    description: 'Customer billed twice for annual Pro subscription on 09/12.',
    amount: '$199.00',
    customer: 'Enterprise #4092'
  },
  {
    id: 't-102',
    title: 'Payment failed',
    category: 'payment',
    dotColor: '#f59e0b', // Amber
    timeAgo: '2m',
    priority: 'Medium',
    description: 'Stripe webhook payment error: Card declined (Code 402).',
    amount: '$49.00',
    customer: 'Acme Corp'
  },
  {
    id: 't-103',
    title: 'Refund for upgrade',
    category: 'refund',
    dotColor: '#10b981', // Mint
    timeAgo: '4m',
    priority: 'Low',
    description: 'Prorated refund request after tier upgrade from Basic to Team.',
    amount: '$85.50',
    customer: 'TechStart Inc'
  },
  {
    id: 't-104',
    title: 'Incorrect tax',
    category: 'tax',
    dotColor: '#10b981', // Mint
    timeAgo: '6m',
    priority: 'Low',
    description: 'EU VAT tax calculation disparity on Invoice #INV-8832.',
    amount: '$14.20',
    customer: 'Global Logistics'
  },
  {
    id: 't-105',
    title: 'Cancel subscription',
    category: 'subscription',
    dotColor: '#10b981', // Mint
    timeAgo: '8m',
    priority: 'Low',
    description: 'User initiated account cancellation, requesting data export.',
    amount: '$0.00',
    customer: 'DevStudio LLC'
  }
];

export const INITIAL_AGENTS = [
  {
    id: 'agent-1',
    name: 'Refund Sentinel',
    role: 'Payment & Escalations Specialist',
    avatarColor: 'orange',
    accentColor: '#f97316',
    baseScore: 88,
    slaSpeed: '< 15s',
    accuracy: '98.6%',
    tagline: 'Specialized in rapid transaction reversals & fraud mitigation.',
    capabilities: ['Duplicate Charge Check', 'Stripe API Gateway', 'Chargeback Shield'],
    thought: 'Analyzing transaction hash... Confirmed duplicate charge signature in audit logs.'
  },
  {
    id: 'agent-2',
    name: 'Billing Bot Alpha',
    role: 'Primary Resolution Engine',
    avatarColor: 'emerald',
    accentColor: '#10b981',
    baseScore: 92,
    slaSpeed: '< 8s',
    accuracy: '99.4%',
    tagline: 'High-precision automated ledger balancing & instant credit allotment.',
    capabilities: ['Ledger Reconcile', 'Tax Code Auditor', 'Auto-Refund Execute'],
    thought: 'Optimal solution found! Alloting ticket for instant ledger refund & client notification.'
  },
  {
    id: 'agent-3',
    name: 'Tax & Compliance Shield',
    role: 'Compliance & Audit Guard',
    avatarColor: 'blue',
    accentColor: '#3b82f6',
    baseScore: 74,
    slaSpeed: '< 25s',
    accuracy: '97.2%',
    tagline: 'Ensures multi-jurisdictional tax compliance and ledger security.',
    capabilities: ['EU VAT Validation', 'Audit Trail Logging', 'Security Vet'],
    thought: 'Calculating compliance index... Validating VAT refund rules across tax zones.'
  }
];

export const RESOLUTION_STEPS_TEMPLATE = [
  { id: 'step-1', name: 'Investigate', timestamp: '10:14', status: 'completed' },
  { id: 'step-2', name: 'Diagnose', timestamp: '10:15', status: 'completed' },
  { id: 'step-3', name: 'Execute', timestamp: '10:15', status: 'completed' },
  { id: 'step-4', name: 'Vet', timestamp: '10:16', status: 'completed' },
  { id: 'step-5', name: 'Done', timestamp: '10:16', status: 'completed' }
];

/**
 * Calculates bids for all 3 agents based on the ticket category & complexity
 */
export function calculateAgentBids(ticket) {
  let a1Score = 88;
  let a2Score = 92;
  let a3Score = 74;

  if (ticket.category === 'billing' || ticket.title.toLowerCase().includes('duplicate')) {
    a1Score = 88;
    a2Score = 95; // Winner
    a3Score = 76;
  } else if (ticket.category === 'payment') {
    a1Score = 94; // Winner
    a2Score = 89;
    a3Score = 78;
  } else if (ticket.category === 'tax') {
    a1Score = 82;
    a2Score = 91;
    a3Score = 96; // Winner
  } else if (ticket.category === 'refund') {
    a1Score = 91;
    a2Score = 93; // Winner
    a3Score = 72;
  } else {
    a1Score = 85;
    a2Score = 92; // Winner
    a3Score = 74;
  }

  return [
    { ...INITIAL_AGENTS[0], bidScore: a1Score },
    { ...INITIAL_AGENTS[1], bidScore: a2Score },
    { ...INITIAL_AGENTS[2], bidScore: a3Score }
  ];
}
