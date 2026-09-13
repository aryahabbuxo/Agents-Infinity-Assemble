import React, { useState, useEffect, useRef } from 'react';
import confetti from 'canvas-confetti';
import Header from './components/Header';
import ResizableSplitter from './components/ResizableSplitter';
import TicketIntakePanel from './components/TicketIntakePanel';
import LiveAuctionPanel from './components/LiveAuctionPanel';
import ResolutionTracePanel from './components/ResolutionTracePanel';
import AgentCallTraceDashboard from './components/AgentCallTraceDashboard';
import InjectTicketModal from './components/InjectTicketModal';
import { 
  INITIAL_AGENTS, 
  RESOLUTION_STEPS_TEMPLATE, 
  calculateAgentBids,
  fetchQueue,
  fetchAgentTrace,
  injectAndTrace,
  executeNextQueueTicket,
  executeEntireQueue,
  resetBackendQueue
} from './services/auctionBackend';

export default function App() {
  // Navigation View State ('market' vs 'trace')
  const [activeView, setActiveView] = useState('market');

  // Panel Width States (% of dashboard grid)
  const [width1, setWidth1] = useState(28); // Ticket Intake %
  const [width2, setWidth2] = useState(44); // Live Auction %
  const [width3, setWidth3] = useState(28); // Resolution Trace %

  // Dynamic Tickets State
  const [tickets, setTickets] = useState([]);
  const [activeTicketId, setActiveTicketId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Auction & Resolution Workflow State
  const [auctionPhase, setAuctionPhase] = useState('intake'); // intake -> bidding -> allotted -> resolving
  const [agents, setAgents] = useState(INITIAL_AGENTS);
  const [steps, setSteps] = useState(RESOLUTION_STEPS_TEMPLATE);
  const [status, setStatus] = useState('PENDING');
  const [winningScore, setWinningScore] = useState(95);

  // Live Backend Data
  const [traceLogs, setTraceLogs] = useState([]);
  const [queueData, setQueueData] = useState({ pending_queue: [], executed_tickets: [], executed_tickets_summary: [] });
  const [agentBalances, setAgentBalances] = useState({});
  const [instanceIndexes, setInstanceIndexes] = useState({});

  const initialLoadDone = useRef(false);

  // Synchronize backend data without interrupting active ticket selection
  const syncBackendData = async () => {
    try {
      const [queueRes, traceRes] = await Promise.all([
        fetchQueue().catch(() => null),
        fetchAgentTrace().catch(() => null),
      ]);

      if (queueRes) {
        const rawPending = (queueRes.pending_queue || []).filter(Boolean).map(t => ({
          id: t.ticket_id || 'T000',
          title: t.title || t.text?.substring(0, 45) || t.ticket_id,
          text: t.text || t.ticket_text || '',
          description: t.text || '',
          category: t.category || 'general',
          dotColor: t.is_rebid ? '#f59e0b' : '#635bff',
          timeAgo: t.is_rebid ? 'Re-bid' : 'Queued',
          is_rebid: t.is_rebid,
          urgency_score: t.urgency_score || 50,
          order_id: t.order_id,
          customer_id: t.customer_id,
        }));

        const rawExecuted = (queueRes.executed_tickets || []).filter(Boolean).map(e => {
          const t = e.ticket || {};
          return {
            id: t.ticket_id || 'T000',
            title: t.title || t.text?.substring(0, 45) || t.ticket_id,
            text: t.text || '',
            description: t.text || '',
            category: t.category || 'general',
            dotColor: '#10b981',
            timeAgo: 'Completed',
            is_rebid: t.is_rebid,
            executedResult: e.result,
          };
        });

        const combined = [...rawPending, ...rawExecuted];
        if (combined.length > 0) {
          setTickets(prev => {
            // Keep in-flight local temp tickets while backend is processing
            const tempTickets = prev.filter(t => t.id.startsWith('T-USER-') && !combined.some(c => c.id === t.id));
            const merged = [...tempTickets, ...combined];
            const uniqueMap = new Map();
            for (const item of merged) {
              uniqueMap.set(item.id, item);
            }
            return Array.from(uniqueMap.values());
          });
          if (!initialLoadDone.current || !activeTicketId) {
            initialLoadDone.current = true;
            selectTicketById(combined[0].id, combined);
          }
        }

        setQueueData(prev => ({
          ...prev,
          pending_queue: queueRes.pending_queue || [],
          executed_tickets: queueRes.executed_tickets || [],
        }));
      }

      if (traceRes) {
        if (Array.isArray(traceRes.trace_logs)) setTraceLogs(traceRes.trace_logs);
        if (traceRes.agent_balances) setAgentBalances(traceRes.agent_balances);
        if (traceRes.instance_indexes) setInstanceIndexes(traceRes.instance_indexes);
        if (Array.isArray(traceRes.executed_tickets_summary)) {
          setQueueData(prev => ({
            ...prev,
            executed_tickets_summary: traceRes.executed_tickets_summary
          }));
        }
      }
    } catch (e) {
      console.warn('Backend sync warning:', e);
    }
  };

  useEffect(() => {
    syncBackendData();
    const interval = setInterval(syncBackendData, 4000);
    return () => clearInterval(interval);
  }, []);

  const activeTicket = tickets.find(t => t.id === activeTicketId) || tickets[0] || null;

  // Handle active ticket selection & bid calculation
  const selectTicketById = async (id, ticketList = tickets) => {
    const ticket = ticketList.find(t => t.id === id);
    if (!ticket) return;

    setActiveTicketId(id);
    setAuctionPhase('intake');
    setSteps(RESOLUTION_STEPS_TEMPLATE.map(s => ({ ...s, status: 'pending' })));
    setStatus('PENDING');

    // Auto-execute unexecuted ticket on backend to generate live trace logs if needed
    if (!ticket.executedResult && ticket.text && !id.startsWith('T-USER-')) {
      const injectRes = await injectAndTrace(ticket.text);
      if (injectRes) {
        if (Array.isArray(injectRes.trace_logs)) setTraceLogs(injectRes.trace_logs);
        if (injectRes.agent_balances) setAgentBalances(injectRes.agent_balances);
        if (injectRes.instance_indexes) setInstanceIndexes(injectRes.instance_indexes);
        if (injectRes.execution_result) {
          ticket.executedResult = injectRes.execution_result;
        }
      }
    }

    const calculatedAgents = calculateAgentBids(ticket, ticket.executedResult || null);
    setAgents(calculatedAgents);

    const topScore = Math.max(...calculatedAgents.map(a => a.bidScore || 80));
    setWinningScore(topScore);
  };

  // Run dynamic UI animation workflow for active ticket
  const runTicketAnimationFlow = (result = null) => {
    setAuctionPhase('intake');
    setSteps(RESOLUTION_STEPS_TEMPLATE.map(s => ({ ...s, status: 'pending' })));
    setStatus('PENDING');

    setTimeout(() => {
      setAuctionPhase('bidding');
    }, 500 / speed);

    setTimeout(() => {
      setAuctionPhase('allotted');
      try {
        confetti({
          particleCount: 45,
          spread: 75,
          origin: { y: 0.65 }
        });
      } catch (e) {}
    }, 1800 / speed);

    setTimeout(() => {
      setAuctionPhase('resolving');
      setSteps(prev => prev.map(s => ({ ...s, status: 'completed' })));
      setStatus('PROCESSED');
    }, 2800 / speed);
  };

  // Add Ticket directly from Ticket Intake input box or modal
  const handleAddTicket = async (ticketText) => {
    if (!ticketText || !ticketText.trim()) return;

    const tempId = `T-USER-${Date.now().toString().slice(-4)}`;
    const newTicketObj = {
      id: tempId,
      title: tempId,
      description: ticketText.trim(),
      text: ticketText.trim(),
      category: 'custom',
      dotColor: '#635bff',
      timeAgo: 'Just now',
      urgency_score: 80,
      is_rebid: false
    };

    setTickets(prev => [newTicketObj, ...prev]);
    setActiveTicketId(tempId);

    // Initial dynamic bid estimation
    const initialAgents = calculateAgentBids(newTicketObj, null);
    setAgents(initialAgents);
    setWinningScore(Math.max(...initialAgents.map(a => a.bidScore || 85)));

    // Start animation sequence
    runTicketAnimationFlow();

    // Call FastAPI backend asynchronously using the atomic endpoint
    const injectRes = await injectAndTrace(ticketText.trim());
    if (injectRes) {
      const backendRes = injectRes.execution_result;
      // Update trace logs immediately with latest data
      setTraceLogs(Array.isArray(injectRes.trace_logs) ? injectRes.trace_logs : []);
      if (injectRes.agent_balances) setAgentBalances(injectRes.agent_balances);
      if (injectRes.instance_indexes) setInstanceIndexes(injectRes.instance_indexes);

      if (backendRes && backendRes.ticket_id) {
        setTickets(prev => prev.map(t => {
          if (t.id === tempId) {
            return {
              ...t,
              id: backendRes.ticket_id,
              title: backendRes.title || backendRes.ticket_id,
              executedResult: backendRes,
              dotColor: '#10b981',
              timeAgo: 'Completed',
            };
          }
          return t;
        }));
        setActiveTicketId(backendRes.ticket_id);
      }

      const realAgents = calculateAgentBids(newTicketObj, backendRes);
      setAgents(realAgents);

      if (backendRes && backendRes.vetting && backendRes.vetting.coverage_score !== undefined) {
        setWinningScore(Math.round(backendRes.vetting.coverage_score * 100));
      } else {
        setWinningScore(Math.max(...realAgents.map(a => a.bidScore || 90)));
      }

      // Refresh queue data
      await syncBackendData();
    }
  };

  const handleInjectModalSubmit = (newTicketObj) => {
    const text = newTicketObj.description || newTicketObj.title;
    handleAddTicket(text);
  };

  // Resizable splitters drag handlers
  const handleDragSplitter1 = (deltaX) => {
    const containerWidth = window.innerWidth;
    const deltaPercentage = (deltaX / containerWidth) * 100;
    const newW1 = Math.max(18, Math.min(50, width1 + deltaPercentage));
    const newW2 = Math.max(25, width2 - deltaPercentage);
    setWidth1(newW1);
    setWidth2(newW2);
  };

  const handleDragSplitter2 = (deltaX) => {
    const containerWidth = window.innerWidth;
    const deltaPercentage = (deltaX / containerWidth) * 100;
    const newW2 = Math.max(25, Math.min(60, width2 + deltaPercentage));
    const newW3 = Math.max(18, 100 - width1 - newW2);
    setWidth2(newW2);
    setWidth3(newW3);
  };

  // Agent Call Trace Dashboard controls
  const handleExecuteNext = async () => {
    const res = await executeNextQueueTicket();
    if (res) {
      if (Array.isArray(res.trace_logs)) setTraceLogs(res.trace_logs);
      if (res.agent_balances) setAgentBalances(res.agent_balances);
      if (res.instance_indexes) setInstanceIndexes(res.instance_indexes);
      const ticketId = res.execution_result?.ticket_id || res.ticket_id;
      if (ticketId) {
        selectTicketById(ticketId);
        runTicketAnimationFlow(res.execution_result || res);
      }
    }
    await syncBackendData();
  };

  const handleExecuteAll = async () => {
    const res = await executeEntireQueue();
    if (res) {
      if (Array.isArray(res.trace_logs)) setTraceLogs(res.trace_logs);
      if (res.agent_balances) setAgentBalances(res.agent_balances);
      if (res.instance_indexes) setInstanceIndexes(res.instance_indexes);
    }
    await syncBackendData();
  };

  const handleResetSimulation = async () => {
    await resetBackendQueue();
    setTickets([]);
    setActiveTicketId(null);
    await syncBackendData();
  };

  // Dynamic Trajectory Flight Path Positioning across Panels
  const intakeCenter = width1 / 2;
  const auctionCenter = width1 + (width2 / 2);
  const traceCenter = width1 + width2 + (width3 / 2);

  let ticketPosLeft = `${intakeCenter}%`;
  let ticketPosTop = '110px';
  let pathD = `M 140 110 Q 250 110 250 110`;

  if (auctionPhase === 'bidding') {
    ticketPosLeft = `${auctionCenter}%`;
    ticketPosTop = '115px';
    pathD = `M 140 110 Q ${intakeCenter * 10} 115 ${auctionCenter * 10} 115`;
  } else if (auctionPhase === 'allotted' || auctionPhase === 'resolving') {
    ticketPosLeft = `${traceCenter}%`;
    ticketPosTop = '110px';
    pathD = `M 140 110 Q ${auctionCenter * 10} 120 ${traceCenter * 10} 110`;
  }

  const isLineVisible = status !== 'PROCESSED';

  return (
    <div className="app-container">
      <Header 
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        speed={speed}
        setSpeed={setSpeed}
        onOpenModal={() => setIsModalOpen(true)}
        onResetSimulation={handleResetSimulation}
        activeView={activeView}
        setActiveView={(view) => {
          setActiveView(view);
          if (view === 'trace') syncBackendData();
        }}
      />

      {activeView === 'market' ? (
        <main className="dashboard-grid">
          {/* PROGRESSIVE TRAJECTORY PATH SVG */}
          <svg className="global-trajectory-canvas" viewBox="0 0 1000 300" preserveAspectRatio="none">
            <path 
              d={pathD} 
              fill="none" 
              stroke="#F0CC7F" 
              strokeWidth="3" 
              strokeDasharray="6 6" 
              opacity={isLineVisible ? 0.9 : 0}
              style={{ 
                transition: 'd 1.8s ease-in-out, opacity 0.8s ease-in-out' 
              }}
            />
          </svg>

          {/* FLOATING COMPACT TICKET BADGE */}
          {activeTicket && (
            <div 
              className="global-flying-ticket"
              style={{
                left: ticketPosLeft,
                top: ticketPosTop,
                transform: 'translate(-50%, -50%)',
                transition: 'left 1.8s cubic-bezier(0.4, 0, 0.2, 1), top 1.8s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              <span 
                className="ticket-dot" 
                style={{ backgroundColor: activeTicket.dotColor || '#635bff', width: 7, height: 7 }} 
              />
              <span>{activeTicket.id}</span>
            </div>
          )}

          {/* Section 1: Ticket Intake Panel */}
          <TicketIntakePanel 
            tickets={tickets}
            activeTicketId={activeTicketId}
            onSelectTicket={(id) => {
              selectTicketById(id);
              runTicketAnimationFlow();
            }}
            onAddTicket={handleAddTicket}
            widthPercentage={width1}
          />

          <ResizableSplitter onDrag={handleDragSplitter1} />

          {/* Section 2: Live Auction Panel */}
          <LiveAuctionPanel 
            activeTicket={activeTicket}
            agents={agents}
            auctionPhase={auctionPhase}
            widthPercentage={width2}
          />

          <ResizableSplitter onDrag={handleDragSplitter2} />

          {/* Section 3: Resolution Trace Panel */}
          <ResolutionTracePanel 
            steps={steps}
            status={status}
            winningScore={winningScore}
            widthPercentage={width3}
          />
        </main>
      ) : (
        <AgentCallTraceDashboard 
          traceLogs={traceLogs}
          queueData={queueData}
          agentBalances={agentBalances}
          instanceIndexes={instanceIndexes}
          onExecuteNext={handleExecuteNext}
          onExecuteAll={handleExecuteAll}
          onResetQueue={handleResetSimulation}
          onRefreshTrace={syncBackendData}
        />
      )}

      <InjectTicketModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onInject={handleInjectModalSubmit}
      />
    </div>
  );
}
