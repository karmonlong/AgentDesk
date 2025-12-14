/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { Presentation, Slide } from '../types';
import { Download, Maximize2, X, ChevronLeft, ChevronRight, Grid, PlaySquare, FileDown, Presentation as PresentationIcon } from 'lucide-react';
// @ts-ignore
import { jsPDF } from "jspdf";
// @ts-ignore
import PptxGenJS from "pptxgenjs";

interface SlideViewerProps {
  presentation: Presentation;
  onReset: () => void;
}

const SlideViewer: React.FC<SlideViewerProps> = ({ presentation, onReset }) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [viewMode, setViewMode] = useState<'carousel' | 'grid'>('carousel');
  const [isExporting, setIsExporting] = useState(false);

  const slides = presentation.slides;
  const currentSlide = slides[currentSlideIndex];

  const nextSlide = () => {
    if (currentSlideIndex < slides.length - 1) setCurrentSlideIndex(prev => prev + 1);
  };

  const prevSlide = () => {
    if (currentSlideIndex > 0) setCurrentSlideIndex(prev => prev - 1);
  };

  const downloadSlide = (slide: Slide) => {
    const link = document.createElement('a');
    link.href = slide.data;
    link.download = `slide-${presentation.topic.substring(0, 10)}-${slide.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportPDF = async () => {
    setIsExporting(true);
    try {
        const doc = new jsPDF({
            orientation: "landscape",
            unit: "px",
            format: [1280, 720] // 16:9 ratio in pixels-ish
        });

        presentation.slides.forEach((slide, index) => {
            if (index > 0) doc.addPage();
            doc.addImage(slide.data, 'PNG', 0, 0, 1280, 720);
        });

        doc.save(`${presentation.topic.replace(/\s+/g, '_')}_presentation.pdf`);
    } catch (e) {
        console.error("PDF Export Failed", e);
        alert("PDF 导出失败，请重试");
    } finally {
        setIsExporting(false);
    }
  };

  const exportPPT = async () => {
    setIsExporting(true);
    try {
        const pres = new PptxGenJS();
        pres.layout = 'LAYOUT_16x9';

        presentation.slides.forEach((slide) => {
            const pptSlide = pres.addSlide();
            // Add image covering the whole slide
            pptSlide.addImage({
                data: slide.data,
                x: 0,
                y: 0,
                w: "100%",
                h: "100%"
            });
            // Optionally add notes if we have them in the future
            if (slide.speakerNotes) {
                pptSlide.addNotes(slide.speakerNotes);
            }
        });

        await pres.writeFile({ fileName: `${presentation.topic.replace(/\s+/g, '_')}.pptx` });
    } catch (e) {
        console.error("PPT Export Failed", e);
        alert("PPT 导出失败，请重试");
    } finally {
        setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700 mt-8 mb-20">
      
      {/* Controls Header */}
      <div className="w-full flex justify-between items-center mb-6 px-2">
         <div>
            <h2 className="text-xl md:text-2xl font-display font-bold text-slate-900 dark:text-white line-clamp-1">
                {presentation.topic}
            </h2>
            <p className="text-xs text-slate-500 font-mono mt-1">
                {slides.length} 页幻灯片 • 由 GEMINI 3 PRO 生成
            </p>
         </div>
         <div className="flex gap-2">
            <button 
                onClick={exportPPT}
                disabled={isExporting}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs transition-colors shadow-lg shadow-orange-500/20"
                title="导出 PPT"
            >
                {isExporting ? '导出中...' : '导出 PPT'}
                <PresentationIcon className="w-4 h-4" />
            </button>
            <button 
                onClick={exportPDF}
                disabled={isExporting}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors shadow-lg shadow-cyan-500/20"
                title="导出 PDF"
            >
                {isExporting ? '导出中...' : '导出 PDF'}
                <FileDown className="w-4 h-4" />
            </button>
            <button 
                onClick={() => setViewMode(viewMode === 'carousel' ? 'grid' : 'carousel')}
                className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                title={viewMode === 'carousel' ? "网格视图" : "轮播视图"}
            >
                {viewMode === 'carousel' ? <Grid className="w-5 h-5 text-slate-600 dark:text-slate-300" /> : <PlaySquare className="w-5 h-5 text-slate-600 dark:text-slate-300" />}
            </button>
         </div>
      </div>

      {viewMode === 'carousel' ? (
        <div className="relative w-full group">
            {/* Main Slide Display */}
            <div className="relative aspect-video w-full bg-slate-900 rounded-2xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-700/50">
                <img 
                    src={currentSlide.data} 
                    alt={currentSlide.title} 
                    className="w-full h-full object-contain"
                />
                
                {/* Overlay Controls */}
                <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <button 
                        onClick={() => setIsFullscreen(true)}
                        className="bg-black/60 backdrop-blur-md text-white p-2 rounded-lg hover:bg-cyan-600 transition-colors"
                        title="全屏"
                    >
                        <Maximize2 className="w-5 h-5" />
                    </button>
                    <button 
                        onClick={() => downloadSlide(currentSlide)}
                        className="bg-black/60 backdrop-blur-md text-white p-2 rounded-lg hover:bg-cyan-600 transition-colors"
                        title="下载单页"
                    >
                        <Download className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation Arrows */}
                <button 
                    onClick={prevSlide}
                    disabled={currentSlideIndex === 0}
                    className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/30 hover:bg-black/60 backdrop-blur-sm text-white disabled:opacity-0 transition-all transform hover:scale-110"
                >
                    <ChevronLeft className="w-8 h-8" />
                </button>
                <button 
                    onClick={nextSlide}
                    disabled={currentSlideIndex === slides.length - 1}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/30 hover:bg-black/60 backdrop-blur-sm text-white disabled:opacity-0 transition-all transform hover:scale-110"
                >
                    <ChevronRight className="w-8 h-8" />
                </button>
            </div>

            {/* Filmstrip */}
            <div className="mt-6 flex gap-3 overflow-x-auto pb-4 px-2 scrollbar-hide snap-x">
                {slides.map((slide, idx) => (
                    <button
                        key={slide.id}
                        onClick={() => setCurrentSlideIndex(idx)}
                        className={`relative flex-shrink-0 w-32 md:w-48 aspect-video rounded-lg overflow-hidden border-2 transition-all snap-center ${
                            idx === currentSlideIndex 
                            ? 'border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-105 z-10' 
                            : 'border-transparent opacity-60 hover:opacity-100'
                        }`}
                    >
                        <img src={slide.data} alt={`Slide ${idx + 1}`} className="w-full h-full object-cover" />
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-[10px] p-1 text-center font-bold">
                            第 {idx + 1} 页
                        </div>
                    </button>
                ))}
            </div>
        </div>
      ) : (
        /* Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
            {slides.map((slide, idx) => (
                <div key={slide.id} className="group relative bg-slate-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-slate-200 dark:border-white/10 shadow-lg hover:shadow-xl transition-all hover:scale-[1.02]">
                    <div className="aspect-video w-full relative">
                         <img src={slide.data} alt={slide.title} className="w-full h-full object-cover" />
                         <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                             <button onClick={() => { setCurrentSlideIndex(idx); setViewMode('carousel'); }} className="bg-white text-slate-900 px-3 py-1.5 rounded-full text-xs font-bold">查看</button>
                             <button onClick={() => downloadSlide(slide)} className="bg-white text-slate-900 p-1.5 rounded-full"><Download className="w-4 h-4"/></button>
                         </div>
                    </div>
                    <div className="p-3">
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-xs font-bold text-cyan-600 dark:text-cyan-400">第 {idx + 1} 页</span>
                        </div>
                        <p className="text-sm font-medium text-slate-900 dark:text-white line-clamp-1">{slide.title}</p>
                    </div>
                </div>
            ))}
        </div>
      )}

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div className="fixed inset-0 z-[100] bg-black flex flex-col items-center justify-center animate-in fade-in duration-300">
            <button 
                onClick={() => setIsFullscreen(false)}
                className="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors z-50"
            >
                <X className="w-6 h-6" />
            </button>
            
            <div className="w-full h-full flex items-center justify-center p-4">
                 <img 
                    src={currentSlide.data} 
                    alt={currentSlide.title}
                    className="max-w-full max-h-full object-contain shadow-2xl"
                />
            </div>
            
            <div className="absolute bottom-8 flex gap-8 items-center z-50">
                <button onClick={prevSlide} disabled={currentSlideIndex === 0} className="text-white/50 hover:text-white disabled:opacity-10">
                    <ChevronLeft className="w-12 h-12" />
                </button>
                <span className="text-white font-mono text-xl">{currentSlideIndex + 1} / {slides.length}</span>
                <button onClick={nextSlide} disabled={currentSlideIndex === slides.length - 1} className="text-white/50 hover:text-white disabled:opacity-10">
                    <ChevronRight className="w-12 h-12" />
                </button>
            </div>
        </div>
      )}
    </div>
  );
};

export default SlideViewer;