import React from 'react';
import { Gavel, Crown, Trophy } from 'lucide-react';
import { OrangeRobot, CrownedGreenRobot, BlueShieldRobot } from './RobotAvatars';

export default function LiveAuctionPanel({ 
  activeTicket, 
  agents, 
  auctionPhase, 
  widthPercentage 
}) {
  // Find winning agent (highest bid score)
  const winningAgent = agents.reduce((prev, current) => 
    ((prev.bidScore || 0) > (current.bidScore || 0)) ? prev : current, agents[0]);

  return (
    <div className="panel-card" style={{ width: `${widthPercentage}%`, position: 'relative' }}>
      <div className="panel-header">
        <div className="panel-title-group">
          <div className="panel-icon-wrap">
            <Gavel size={24} />
          </div>
          <h2 className="panel-title">Live Auction</h2>
        </div>
      </div>

      {/* Stage Lifecycle Pills Bar */}
      <div className="auction-stage-bar">
        <div className="stage-line" />
        <span className={`auction-stage-pill stage-propose ${auctionPhase === 'bidding' ? 'active-pill' : ''}`}>
          PROPOSE
        </span>
        <span className={`auction-stage-pill stage-accept ${auctionPhase === 'allotted' ? 'active-pill' : ''}`}>
          ACCEPT
        </span>
        <span className="auction-stage-pill stage-counter">
          COUNTER
        </span>
      </div>

      {/* Dedicated Gap Area where the flying ticket pauses HIGH ABOVE THE AGENTS */}
      <div className="auction-waiting-gap" />

      {/* Agent Podiums Section */}
      <div className="podiums-container">
        {/* Agent 1 (Left - Potting Soil & Sceptre Red) */}
        <div className={`agent-podium-wrapper ${agents[0]?.id === winningAgent?.id ? 'winner' : ''}`}>
          {agents[0]?.id === winningAgent?.id && (
            <div className="winner-crown">
              <Crown size={30} color="#4D0E12" fill="#F5EFC6" />
            </div>
          )}
          <div className={`bid-paddle ${agents[0]?.id === winningAgent?.id ? 'winner-paddle' : ''}`}>
            {agents[0]?.bidScore || 88}
          </div>
          <OrangeRobot />
          <div className={`podium-base ${agents[0]?.id === winningAgent?.id ? 'winner-base' : ''}`} />
        </div>

        {/* Agent 2 (Center Winner - Sceptre Red & Transparent Yellow) */}
        <div className={`agent-podium-wrapper ${agents[1]?.id === winningAgent?.id ? 'winner' : ''}`}>
          {agents[1]?.id === winningAgent?.id && (
            <div className="winner-crown">
              <Crown size={30} color="#4D0E12" fill="#F5EFC6" />
            </div>
          )}
          <div className={`bid-paddle ${agents[1]?.id === winningAgent?.id ? 'winner-paddle' : ''}`}>
            {agents[1]?.bidScore || 95}
          </div>
          <CrownedGreenRobot />
          <div className={`podium-base ${agents[1]?.id === winningAgent?.id ? 'winner-base' : ''}`} />
        </div>

        {/* Agent 3 (Right - Cerulean Blue & Potting Soil) */}
        <div className={`agent-podium-wrapper ${agents[2]?.id === winningAgent?.id ? 'winner' : ''}`}>
          {agents[2]?.id === winningAgent?.id && (
            <div className="winner-crown">
              <Crown size={30} color="#4D0E12" fill="#F5EFC6" />
            </div>
          )}
          <div className={`bid-paddle ${agents[2]?.id === winningAgent?.id ? 'winner-paddle' : ''}`}>
            {agents[2]?.bidScore || 76}
          </div>
          <BlueShieldRobot />
          <div className={`podium-base ${agents[2]?.id === winningAgent?.id ? 'winner-base' : ''}`} />
        </div>
      </div>

      {/* ALL AGENTS' BIDS SUMMARY BOX WITH HIGHLIGHTED WINNER */}
      <div className="agent-bids-summary-box">
        <div className="bids-summary-header">
          <span className="bids-summary-title">⚡ Live Auction Bids Breakdown</span>
          <span className="bids-summary-subtitle">Multi-agent suitability & domain score</span>
        </div>

        <div className="agents-bids-grid">
          {agents.map((agent) => {
            const isWinner = agent.id === winningAgent.id;
            return (
              <div 
                key={agent.id} 
                className={`agent-bid-card ${isWinner ? 'winner-card' : ''}`}
              >
                <div className="agent-bid-header">
                  <span className="agent-name">{agent.name}</span>
                  {isWinner ? (
                    <span className="winner-badge">
                      <Trophy size={12} /> WINNER
                    </span>
                  ) : (
                    <span className="bid-tag">Bid</span>
                  )}
                </div>

                <div className="agent-bid-score">
                  <span className="score-val">{agent.bidScore}</span>
                  <span className="score-max">/ 100</span>
                </div>

                <div className="agent-meta">
                  <span>SLA: {agent.slaSpeed}</span>
                </div>

                <p className="agent-thought-text">
                  "{agent.thought}"
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
