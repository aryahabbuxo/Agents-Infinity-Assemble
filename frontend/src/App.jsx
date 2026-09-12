import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import Header from './components/Header';
import ResizableSplitter from './components/ResizableSplitter';
import TicketIntakePanel from './components/TicketIntakePanel';
import LiveAuctionPanel from './components/LiveAuctionPanel';
import ResolutionTracePanel from './components/ResolutionTracePanel';
import InjectTicketModal from './components/InjectTicketModal';
import { 
  INITIAL_TICKETS, 
  INITIAL_AGENTS, 
  RESOLUTION_STEPS_TEMPLATE, 
  calculateAgentBids 
} from './services/auctionBackend';

export default function App() {
  // Panel Width States (Extendable sections)
  const [width1, setWidth1] = useState(28); // Ticket Intake %
  const [width2, setWidth2] = useState(44); // Live Auction %
  const [width3, setWidth3] = useState(28); // Resolution Trace %

  // Simulation Data State
  const [tickets, setTickets] = useState(INITIAL_TICKETS);
  const [activeTicketId, setActiveTicketId] = useState('t-101');
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Auction & Resolution Workflow State (MUST START AT 'intake' SO FLOW STARTS IN ZONE 1!)
  const [auctionPhase, setAuctionPhase] = useState('intake'); // intake -> bidding -> allotted -> resolving
  const [agents, setAgents] = useState(() => calculateAgentBids(INITIAL_TICKETS[0]));
  const [steps, setSteps] = useState(RESOLUTION_STEPS_TEMPLATE);
  const [status, setStatus] = useState('PENDING');

  const activeTicket = tickets.find(t => t.id === activeTicketId) || tickets[0];

  // Handle active ticket change & recalculate agent bids
  const handleSelectTicket = (id) => {
    const ticket = tickets.find(t => t.id === id);
    if (!ticket) return;
    setActiveTicketId(id);
    setAuctionPhase('intake');
    setSteps(RESOLUTION_STEPS_TEMPLATE.map(s => ({ ...s, status: 'pending' })));
    setStatus('PENDING');

    setTimeout(() => {
      setAgents(calculateAgentBids(ticket));
    }, 400);
  };

  // Main Simulation Step Timer Loop
  useEffect(() => {
    if (!isPlaying) return;

    const intervalMs = 3600 / speed;
    const timer = setInterval(() => {
      if (auctionPhase === 'intake') {
        setAuctionPhase('bidding');
      } else if (auctionPhase === 'bidding') {
        setAuctionPhase('allotted');
        confetti({
          particleCount: 35,
          spread: 70,
          origin: { y: 0.65 }
        });
      } else if (auctionPhase === 'allotted') {
        setAuctionPhase('resolving');
        setSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'completed' } : s));
      } else if (auctionPhase === 'resolving') {
        setSteps(prev => {
          const nextIndex = prev.findIndex(s => s.status !== 'completed');
          if (nextIndex !== -1) {
            const updated = [...prev];
            updated[nextIndex] = { ...updated[nextIndex], status: 'completed' };
            return updated;
          } else {
            setStatus('PROCESSED');
            return prev;
          }
        });
      }
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, speed, auctionPhase]);

  // Handle Dragging Splitters
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

  // Inject New Ticket
  const handleInjectTicket = (newTicket) => {
    setTickets(prev => [newTicket, ...prev]);
    handleSelectTicket(newTicket.id);
  };

  // Reset Simulation
  const handleResetSimulation = () => {
    setTickets(INITIAL_TICKETS);
    handleSelectTicket('t-101');
  };

  // Flight Path Position Calculations:
  // Starts strictly in Zone 1 (Intake left 14%, top 110px)
  // Glides into Zone 2 (Auction center 50%, top 115px - below pills, zero overlap)
  // Glides into Zone 3 (Resolution right 86%, top 110px)
  let ticketPosStyle = { left: '14%', top: '110px' };
  let pathD = "M 140 110 Q 250 112 250 112";

  if (auctionPhase === 'bidding') {
    ticketPosStyle = { left: '50%', top: '115px' };
    pathD = "M 140 110 Q 320 115 500 115";
  } else if (auctionPhase === 'allotted' || auctionPhase === 'resolving') {
    ticketPosStyle = { left: '86%', top: '110px' };
    pathD = "M 140 110 Q 500 120 860 110";
  }

  // Dotted Line disappears once ticket reaches Zone 3 & status is PROCESSED!
  const isLineVisible = status !== 'PROCESSED';

  // Calculate winning score
  const winningScore = Math.max(...agents.map(a => a.bidScore || 92));

  return (
    <div className="app-container">
      <Header 
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        speed={speed}
        setSpeed={setSpeed}
        onOpenModal={() => setIsModalOpen(true)}
        onResetSimulation={handleResetSimulation}
      />

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
              transition: 'd 2.4s ease-in-out, opacity 0.8s ease-in-out' 
            }}
          />
        </svg>

        {/* FLOATING COMPACT TICKET BADGE */}
        {activeTicket && (
          <div 
            className="global-flying-ticket"
            style={{
              left: ticketPosStyle.left,
              top: ticketPosStyle.top,
              transform: 'translate(-50%, -50%)',
              transition: 'left 2.4s cubic-bezier(0.4, 0, 0.2, 1), top 2.4s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          >
            <span 
              className="ticket-dot" 
              style={{ backgroundColor: activeTicket.dotColor, width: 7, height: 7 }} 
            />
            <span>{activeTicket.title}</span>
          </div>
        )}

        {/* Section 1: Ticket Intake Panel */}
        <TicketIntakePanel 
          tickets={tickets}
          activeTicketId={activeTicketId}
          onSelectTicket={handleSelectTicket}
          widthPercentage={width1}
        />

        {/* Extendable Resizable Handle 1 */}
        <ResizableSplitter onDrag={handleDragSplitter1} />

        {/* Section 2: Live Auction Panel */}
        <LiveAuctionPanel 
          activeTicket={activeTicket}
          agents={agents}
          auctionPhase={auctionPhase}
          widthPercentage={width2}
        />

        {/* Extendable Resizable Handle 2 */}
        <ResizableSplitter onDrag={handleDragSplitter2} />

        {/* Section 3: Resolution Trace Panel */}
        <ResolutionTracePanel 
          steps={steps}
          status={status}
          winningScore={winningScore}
          widthPercentage={width3}
        />
      </main>

      <InjectTicketModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onInject={handleInjectTicket}
      />
    </div>
  );
}
