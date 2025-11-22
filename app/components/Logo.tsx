import React from 'react';

interface LogoProps {
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ className }) => {
  return (
    <svg 
      viewBox="0 0 512 512" 
      xmlns="http://www.w3.org/2000/svg" 
      className={className}
      fill="none" // Allow controlling fill via class if needed, though internal elements have fills
    >
      {/* 1. Background: IITM Maroon Rounded Square - Removed to allow transparent background usage or custom container */}
      {/* If background is needed, uncomment or handle in container */}
      {/* <rect x="0" y="0" width="512" height="512" rx="100" ry="100" fill="#6E263D"/> */}
      
      {/* Actually, for a logo component, usually we want the shape. The user provided a background rect. 
          I will keep it but maybe allow className to hide it? Or just keep it as the official logo background.
          Let's keep the full SVG as provided for now, maybe scaling it.
      */}
      <rect x="0" y="0" width="512" height="512" rx="100" ry="100" fill="#6E263D"/>

      {/* 2. The Digital Pulse (Lightning replacement) */}
      <polyline points="140,440 200,440 230,410 280,470 310,440 372,440" 
                fill="none" stroke="white" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/>

      {/* 3. The Diya Base (Geometric/Data Blocks) */}
      <path d="M120 320 Q 256 460 392 320 Z" fill="#D4AF37"/>
      {/* Data Block Details on Base */}
      <path d="M120 320 L 392 320" stroke="#4a192c" strokeWidth="4"/>
      <rect x="200" y="340" width="30" height="20" fill="#B8860B"/>
      <rect x="280" y="340" width="30" height="20" fill="#B8860B"/>
      <rect x="240" y="370" width="30" height="20" fill="#B8860B"/>

      {/* 4. The Neural Flame (Teardrop Shape) */}
      {/* Outer Glow */}
      <path d="M256 60 Q 380 200 380 320 H 132 Q 132 200 256 60 Z" fill="#112233" opacity="0.6"/>
      
      {/* Neural Network Connections (Cyan Lines) */}
      <g stroke="#00FFFF" strokeWidth="3" strokeLinecap="round">
        <line x1="256" y1="100" x2="200" y2="180" />
        <line x1="256" y1="100" x2="312" y2="180" />
        <line x1="200" y1="180" x2="200" y2="280" />
        <line x1="312" y1="180" x2="312" y2="280" />
        <line x1="200" y1="280" x2="256" y2="250" />
        <line x1="312" y1="280" x2="256" y2="250" />
        <line x1="256" y1="100" x2="256" y2="180" />
      </g>

      {/* 5. The PCB Lotus (Gold Circuit Tracks) */}
      <g stroke="#FFD700" strokeWidth="4" fill="none" strokeLinecap="round">
         {/* Left Petal Circuit */}
         <path d="M 256 320 Q 180 300 180 220 Q 200 180 256 220" />
         <line x1="200" y1="250" x2="220" y2="250" strokeWidth="2"/>
         <circle cx="200" cy="250" r="4" fill="#FFD700" stroke="none"/>

         {/* Right Petal Circuit */}
         <path d="M 256 320 Q 332 300 332 220 Q 312 180 256 220" />
         <line x1="312" y1="250" x2="292" y2="250" strokeWidth="2"/>
         <circle cx="312" cy="250" r="4" fill="#FFD700" stroke="none"/>

         {/* Center Petal Circuit */}
         <path d="M 256 320 L 256 150" strokeDasharray="10,5"/>
      </g>

      {/* 6. The Eye/Core (Siddhi/Mascot) */}
      <circle cx="256" cy="250" r="25" fill="#FFFFFF" stroke="#00FFFF" strokeWidth="4"/>
      <circle cx="256" cy="250" r="10" fill="#6E263D" stroke="none"/>
      
      {/* Neural Nodes (Dots) */}
      <circle cx="256" cy="100" r="6" fill="#00FFFF" stroke="none"/>
      <circle cx="200" cy="180" r="6" fill="#00FFFF" stroke="none"/>
      <circle cx="312" cy="180" r="6" fill="#00FFFF" stroke="none"/>
      <circle cx="200" cy="280" r="6" fill="#00FFFF" stroke="none"/>
      <circle cx="312" cy="280" r="6" fill="#00FFFF" stroke="none"/>
    </svg>
  );
};

export default Logo;
