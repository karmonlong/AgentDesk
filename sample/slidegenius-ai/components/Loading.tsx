/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React from 'react';
import { Loader2, Layout, Image as ImageIcon, Sparkles } from 'lucide-react';

interface LoadingProps {
  status: string;
  step: number; // 1 = analyzing, 2 = generating
  facts?: string[];
}

const Loading: React.FC<LoadingProps> = ({ status, step }) => {
  return (
    <div className="relative flex flex-col items-center justify-center w-full max-w-4xl mx-auto mt-8 min-h-[400px] overflow-hidden rounded-3xl bg-white/40 dark:bg-slate-900/40 border border-slate-200 dark:border-white/10 shadow-2xl backdrop-blur-md">
      
      {/* Progress Visualization */}
      <div className="flex items-center gap-4 md:gap-8 mb-12 relative z-10">
          
          {/* Node 1: Analysis */}
          <div className="flex flex-col items-center gap-2">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${step >= 1 ? 'bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.5)]' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
                  <Layout className="w-5 h-5" />
              </div>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${step >= 1 ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-500'}`}>生成大纲</span>
          </div>

          {/* Connector */}
          <div className="w-16 h-1 bg-slate-800 relative overflow-hidden rounded-full">
              <div className={`absolute inset-0 bg-cyan-500 transition-all duration-1000 ${step >= 2 ? 'w-full' : 'w-0'}`}></div>
          </div>

          {/* Node 2: Generation */}
          <div className="flex flex-col items-center gap-2">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${step >= 2 ? 'bg-purple-600 border-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)]' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
                  <ImageIcon className="w-5 h-5" />
              </div>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${step >= 2 ? 'text-purple-600 dark:text-purple-400' : 'text-slate-500'}`}>绘制幻灯片</span>
          </div>
      </div>

      <div className="text-center space-y-4 px-6 max-w-lg z-10">
          <div className="flex items-center justify-center gap-3 text-slate-900 dark:text-white">
             <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
             <h3 className="text-xl font-bold font-display">{status}</h3>
          </div>
          <p className="text-sm text-slate-500">
             使用 Gemini 3 Pro (Nano Banana Pro) 分析内容并生成专业设计...
          </p>
      </div>

      {/* Decorative Background */}
      <div className="absolute inset-0 pointer-events-none opacity-20 dark:opacity-10">
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full blur-[100px] animate-pulse"></div>
      </div>

    </div>
  );
};

export default Loading;