import React from 'react';

// Agent 1: Soft Green (#738262) & Butter Yellow (#F0CC7F)
export function OrangeRobot() {
  return (
    <svg viewBox="0 0 100 100" className="robot-avatar">
      {/* Head */}
      <rect x="25" y="25" width="50" height="40" rx="10" fill="#F0CC7F" stroke="#445C70" strokeWidth="4" />
      {/* Ears */}
      <circle cx="20" cy="45" r="7" fill="#738262" stroke="#445C70" strokeWidth="3" />
      <circle cx="80" cy="45" r="7" fill="#738262" stroke="#445C70" strokeWidth="3" />
      {/* Antenna */}
      <line x1="50" y1="25" x2="50" y2="14" stroke="#445C70" strokeWidth="4" strokeLinecap="round" />
      <circle cx="50" cy="11" r="5" fill="#DD8B5C" stroke="#445C70" strokeWidth="3" />
      {/* Face Screen */}
      <rect x="32" y="33" width="36" height="24" rx="6" fill="#445C70" />
      {/* Eyes */}
      <circle cx="42" cy="45" r="4.5" fill="#F0CC7F" />
      <circle cx="58" cy="45" r="4.5" fill="#F0CC7F" />
      {/* Body */}
      <path d="M 30 65 Q 50 63 70 65 L 66 90 Q 50 94 34 90 Z" fill="#738262" stroke="#445C70" strokeWidth="4" strokeLinejoin="round" />
      <rect x="42" y="70" width="16" height="12" rx="3" fill="#E5B49E" stroke="#445C70" strokeWidth="3" />
    </svg>
  );
}

// Agent 2 (Winner): Sun Oranges (#DD8B5C), Butter Yellow (#F0CC7F), Pink Skies (#E5B49E)
export function CrownedGreenRobot() {
  return (
    <svg viewBox="0 0 100 100" className="robot-avatar">
      {/* Cape */}
      <path d="M 20 62 Q 50 55 80 62 L 84 94 Q 50 100 16 94 Z" fill="#E5B49E" stroke="#445C70" strokeWidth="2.5" />
      {/* Head */}
      <rect x="23" y="24" width="54" height="42" rx="12" fill="#F0CC7F" stroke="#445C70" strokeWidth="4" />
      {/* Ears */}
      <rect x="15" y="38" width="8" height="14" rx="3" fill="#DD8B5C" stroke="#445C70" strokeWidth="3" />
      <rect x="77" y="38" width="8" height="14" rx="3" fill="#DD8B5C" stroke="#445C70" strokeWidth="3" />
      {/* Face Screen */}
      <rect x="30" y="32" width="40" height="26" rx="8" fill="#445C70" />
      {/* Eyes */}
      <path d="M 38 46 Q 43 40 48 46" fill="none" stroke="#F0CC7F" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M 52 46 Q 57 40 62 46" fill="none" stroke="#F0CC7F" strokeWidth="3.5" strokeLinecap="round" />
      {/* Smile */}
      <path d="M 46 52 Q 50 55 54 52" fill="none" stroke="#F0CC7F" strokeWidth="2.5" strokeLinecap="round" />
      {/* Body */}
      <path d="M 28 66 Q 50 63 72 66 L 68 92 Q 50 96 32 92 Z" fill="#DD8B5C" stroke="#445C70" strokeWidth="4" strokeLinejoin="round" />
      <circle cx="50" cy="78" r="7" fill="#F0CC7F" stroke="#445C70" strokeWidth="3" />
    </svg>
  );
}

// Agent 3: Pink Skies (#E5B49E) & Soft Green (#738262)
export function BlueShieldRobot() {
  return (
    <svg viewBox="0 0 100 100" className="robot-avatar">
      {/* Head */}
      <rect x="26" y="26" width="48" height="38" rx="10" fill="#E5B49E" stroke="#445C70" strokeWidth="4" />
      {/* Curved Antenna */}
      <path d="M 50 26 C 50 18 58 14 62 10" fill="none" stroke="#445C70" strokeWidth="3.5" strokeLinecap="round" />
      <circle cx="63" cy="9" r="4.5" fill="#F0CC7F" stroke="#445C70" strokeWidth="2.5" />
      {/* Face Screen */}
      <rect x="34" y="34" width="32" height="22" rx="6" fill="#445C70" />
      {/* Eyes */}
      <circle cx="43" cy="45" r="4" fill="#F0CC7F" />
      <circle cx="57" cy="45" r="4" fill="#F0CC7F" />
      {/* Body */}
      <path d="M 32 64 Q 50 62 68 64 L 64 88 Q 50 92 36 88 Z" fill="#738262" stroke="#445C70" strokeWidth="4" strokeLinejoin="round" />
      {/* Shield emblem on chest */}
      <path d="M 45 70 L 55 70 L 55 77 L 50 82 L 45 77 Z" fill="#F0CC7F" stroke="#445C70" strokeWidth="2.5" />
    </svg>
  );
}
