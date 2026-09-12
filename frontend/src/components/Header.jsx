import React from 'react';
import { Bot, Play, Pause, FastForward, PlusCircle, RefreshCw } from 'lucide-react';

export default function Header({ 
  isPlaying, 
  setIsPlaying, 
  speed, 
  setSpeed, 
  onOpenModal,
  onResetSimulation
}) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon">
          <Bot size={22} />
        </div>
        <div>
          <h1 className="brand-title">Autonomous Agent Ticket Auction & Resolution Engine</h1>
          <p className="brand-subtitle">Real-time multi-agent bidding and automated resolution workflow</p>
        </div>
      </div>

      <div className="header-controls">
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
