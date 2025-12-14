/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useEffect } from 'react';
import { Play, Presentation, Sparkles } from 'lucide-react';

interface IntroScreenProps {
  onComplete: () => void;
}

const IntroScreen: React.FC<IntroScreenProps> = ({ onComplete }) => {
  const [phase, setPhase] = useState(0); 
  
  useEffect(() => {
    const timer1 = setTimeout(() => setPhase(1), 1000); 
    const timer2 = setTimeout(() => setPhase(2), 2500); 
    const timer3 = setTimeout(() => setPhase(3), 4000); 

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  const handleEnter = () => {
    onComplete();
  };

  return (
    <div className="fixed inset-0 z-[100] bg-slate-950 flex flex-col items-center justify-center overflow-hidden font-display">
      {/* Background FX */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-900/40 via-slate-950 to-black"></div>
      
      <div className="relative z-10 flex flex-col items-center">
         
         <div className="relative w-32 h-32 md:w-48 md:h-48 mb-8 flex items-center justify-center">
            {/* Animated Stack */}
            <div className={`absolute w-full h-full border border-cyan-500/30 bg-slate-900/50 rounded-xl transition-all duration-700 ${phase >= 1 ? 'rotate-[-10deg] translate-x-[-20px] opacity-100' : 'opacity-0'}`}></div>
            <div className={`absolute w-full h-full border border-cyan-500/30 bg-slate-900/50 rounded-xl transition-all duration-700 delay-100 ${phase >= 2 ? 'rotate-[10deg] translate-x-[20px] opacity-100' : 'opacity-0'}`}></div>
            
            {/* Main Card */}
            <div className={`relative w-full h-full bg-gradient-to-br from-cyan-600 to-blue-700 rounded-xl shadow-[0_0_50px_rgba(6,182,212,0.4)] flex items-center justify-center transition-all duration-1000 ${phase >= 0 ? 'scale-100 opacity-100' : 'scale-50 opacity-0'}`}>
                <Presentation className="w-16 h-16 text-white" />
                <div className="absolute -top-2 -right-2">
                    <Sparkles className="w-8 h-8 text-amber-400 animate-pulse" />
                </div>
            </div>
         </div>

         <div className={`text-center space-y-4 transition-all duration-1000 ${phase >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <h1 className="text-4xl md:text-6xl font-bold text-white tracking-tight">
                SlideGenius <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-amber-400">AI</span>
            </h1>
            <p className="text-slate-400 text-sm md:text-base max-w-md mx-auto leading-relaxed">
                只需几秒，将任何文章、主题转化为专业演示文稿。
            </p>
            
            <button 
                onClick={handleEnter}
                className="mt-8 px-8 py-4 bg-white text-slate-950 rounded-full font-bold tracking-wider hover:bg-cyan-50 transition-colors flex items-center gap-2 mx-auto"
            >
                开始制作 <Play className="w-4 h-4 fill-current" />
            </button>
         </div>

      </div>
    </div>
  );
};

export default IntroScreen;