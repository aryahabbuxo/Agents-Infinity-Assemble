import React from 'react';
import { Bot, Play, Pause, FastForward, PlusCircle, RefreshCw, Activity, Layers } from 'lucide-react';

export default function Header({ 
  isPlaying, 
  setIsPlaying, 
  speed, 
  setSpeed, 
  onOpenModal,
  onResetSimulation,
  activeView,
  setActiveView
}) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon">
          <Bot size={22} />
        </div>
        <div>
          <h1 className="brand-title">Autonomous Agent Ticket Auction & Resolution Engine</h1>
          <p className="brand-subtitle">Real-time multi-agent bidding, coverage vetting & live execution market</p>
        </div>
      </div>

      <div className="header-controls">
        {/* VIEW NAVIGATION TOGGLE BUTTONS */}
        <div className="view-toggle-group">
          <button 
            className={`btn-pill ${activeView === 'market' ? 'btn-view-active' : ''}`}
            onClick={() => setActiveView('market')}
            title="Market Auction & Resolution View"
          >
            <Layers size={16} />
            <span>Market View</span>
          </button>
          
          <button 
            className={`btn-pill ${activeView === 'trace' ? 'btn-view-active' : ''}`}
            onClick={() => setActiveView('trace')}
            title="Agent Call Trace & Execution Terminal"
          >
            <Activity size={16} color="#10b981" />
            <span>Agent Call Trace</span>
          </button>
        </div>

        <button 
          className="btn-pill"
          onClick={() => setIsPlaying(!isPlaying)}
          title={isPlaying ? "Pause Simulation" : "Play Simulation"}
        >
          {isPlaying ? <Pause size={16} color="#ef4444" /> : <Play size={16} color="#10b981" />}
          <span>{isPlaying ? "Pause Engine" : "Resume Engine"}</span>
        </button>

        <button 
          className="btn-pill"
          onClick={() => {
            const speeds = [1, 2, 5];
            const nextSpeed = speeds[(speeds.indexOf(speed) + 1) % speeds.length];
            setSpeed(nextSpeed);
          }}
          title="Change Simulation Speed"
        >
          <FastForward size={16} color="#635bff" />
          <span>{speed}x Speed</span>
        </button>

        <button 
          className="btn-pill"
          onClick={onResetSimulation}
          title="Reset Simulation Data"
        >
          <RefreshCw size={16} />
          <span>Reset</span>
        </button>

        <button 
          className="btn-pill btn-primary"
          onClick={onOpenModal}
        >
          <PlusCircle size={16} />
          <span>Inject Ticket</span>
        </button>
      </div>
    </header>
  );
}
