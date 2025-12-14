/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useEffect, useRef } from 'react';
import { Presentation, ComplexityLevel, VisualStyle, Language, Slide, UploadedFile } from './types';
import { 
  generatePresentationOutline, 
  generateSlideImage, 
} from './services/geminiService';
import SlideViewer from './components/Infographic';
import Loading from './components/Loading';
import IntroScreen from './components/IntroScreen';
import SearchResults from './components/SearchResults';
import { Presentation as PresentationIcon, AlertCircle, Sparkles, GraduationCap, Palette, Globe, Sun, Moon, Key, CreditCard, ExternalLink, DollarSign, FileText, Paperclip, X, File as FileIcon, Layers } from 'lucide-react';
// @ts-ignore
import mammoth from 'mammoth';

const App: React.FC = () => {
  const [showIntro, setShowIntro] = useState(true);
  
  // Input State
  const [inputText, setInputText] = useState('');
  const [complexityLevel, setComplexityLevel] = useState<ComplexityLevel>('专业');
  const [visualStyle, setVisualStyle] = useState<VisualStyle>('现代简约');
  const [language, setLanguage] = useState<Language>('简体中文');
  const [slideCount, setSlideCount] = useState<number>(5);
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  
  // Processing State
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [loadingStep, setLoadingStep] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  
  // Results State
  const [presentation, setPresentation] = useState<Presentation | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(true);

  // API Key State
  const [hasApiKey, setHasApiKey] = useState(false);
  const [checkingKey, setCheckingKey] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Check for API Key on Mount
  useEffect(() => {
    const checkKey = async () => {
      try {
        if (window.aistudio && window.aistudio.hasSelectedApiKey) {
          const hasKey = await window.aistudio.hasSelectedApiKey();
          setHasApiKey(hasKey);
        } else {
          setHasApiKey(true);
        }
      } catch (e) {
        console.error("Error checking API key:", e);
      } finally {
        setCheckingKey(false);
      }
    };
    checkKey();
  }, []);

  const handleSelectKey = async () => {
    if (window.aistudio && window.aistudio.openSelectKey) {
      try {
        await window.aistudio.openSelectKey();
        setHasApiKey(true);
        setError(null);
      } catch (e) {
        console.error("Failed to open key selector:", e);
      }
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset current file state
    setUploadedFile(null);
    setError(null);

    try {
        // PDF Handling
        if (file.type === 'application/pdf') {
            const reader = new FileReader();
            reader.onload = (e) => {
                const base64 = e.target?.result as string;
                // Strip the data:application/pdf;base64, prefix
                const data = base64.split(',')[1];
                setUploadedFile({
                    name: file.name,
                    type: file.type,
                    data: data
                });
            };
            reader.readAsDataURL(file);
        } 
        // Word Document Handling
        else if (file.name.endsWith('.docx') || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const arrayBuffer = e.target?.result as ArrayBuffer;
                try {
                    const result = await mammoth.extractRawText({ arrayBuffer });
                    setInputText(prev => prev + (prev ? '\n\n' : '') + `[内容来自 ${file.name}]:\n` + result.value);
                } catch (err) {
                    setError("无法提取 Word 文档内容");
                    console.error(err);
                }
            };
            reader.readAsArrayBuffer(file);
        }
        // Text File Handling
        else if (file.type === 'text/plain') {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                setInputText(prev => prev + (prev ? '\n\n' : '') + `[内容来自 ${file.name}]:\n` + text);
            };
            reader.readAsText(file);
        } else {
            setError("不支持的文件类型。请上传 PDF, DOCX, 或 TXT。");
        }
    } catch (err) {
        console.error("File upload error", err);
        setError("文件处理出错");
    } finally {
        // Clear input so same file can be selected again if needed
        if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    if (!inputText.trim() && !uploadedFile) {
        setError("请输入主题，粘贴文本，或上传文件。");
        return;
    }

    setIsLoading(true);
    setError(null);
    setLoadingStep(1);
    setLoadingMessage(`正在分析内容并构建 ${slideCount} 页大纲...`);

    try {
      // Step 1: Generate Outline
      const { outline, sources } = await generatePresentationOutline(
          inputText, 
          uploadedFile, 
          complexityLevel, 
          visualStyle, 
          language,
          slideCount
      );
      
      setLoadingStep(2);
      setLoadingMessage(`正在并行绘制 ${outline.length} 页幻灯片...`);
      
      // Step 2: Generate all slides in parallel
      const slidePromises = outline.map(async (slideOutline, index) => {
        const base64 = await generateSlideImage(slideOutline);
        return {
            id: `slide-${index}`,
            title: slideOutline.title,
            data: base64,
            speakerNotes: slideOutline.content
        } as Slide;
      });

      const slides = await Promise.all(slidePromises);
      
      const newPresentation: Presentation = {
        id: Date.now().toString(),
        topic: outline[0].title || "Generated Presentation",
        timestamp: Date.now(),
        slides: slides,
        level: complexityLevel,
        style: visualStyle,
        sources: sources
      };

      setPresentation(newPresentation);
      setUploadedFile(null); // Clear file after generation
    } catch (err: any) {
      console.error(err);
      if (err.message && (err.message.includes("Requested entity was not found") || err.message.includes("404") || err.message.includes("403"))) {
          setError("访问被拒绝。请选择启用了计费的 Google Cloud 项目 API 密钥。");
          setHasApiKey(false);
      } else {
          setError('生成失败。请尝试缩短文本或更换主题。');
      }
    } finally {
      setIsLoading(false);
      setLoadingStep(0);
    }
  };

  const resetApp = () => {
    setPresentation(null);
  };

  // Modal for API Key Selection
  const KeySelectionModal = () => (
    <div className="fixed inset-0 z-[200] bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-300">
        <div className="bg-white dark:bg-slate-900 border-2 border-amber-500/50 rounded-2xl shadow-2xl max-w-md w-full p-6 md:p-8 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500"></div>
            
            <div className="flex flex-col items-center text-center space-y-6">
                <div className="relative">
                    <div className="w-20 h-20 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center text-amber-600 dark:text-amber-400 mb-2 border-4 border-white dark:border-slate-900 shadow-lg">
                        <CreditCard className="w-8 h-8" />
                    </div>
                </div>
                
                <div className="space-y-3">
                    <h2 className="text-2xl font-display font-bold text-slate-900 dark:text-white">
                        需付费 API 密钥
                    </h2>
                    <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed font-medium">
                        本应用使用高级 Gemini 3 Pro 模型。
                    </p>
                    <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                        您必须选择一个 <span className="font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-1 py-0.5 rounded">启用了计费</span> 的 Google Cloud 项目。
                    </p>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl p-4 w-full text-left">
                    <div className="flex items-start gap-3">
                         <div className="p-1.5 bg-amber-100 dark:bg-amber-900/30 rounded-lg text-amber-600 dark:text-amber-400 shrink-0">
                            <DollarSign className="w-4 h-4" />
                         </div>
                         <div className="space-y-1">
                            <p className="text-xs font-bold text-slate-900 dark:text-slate-200">必须启用计费</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                免费的 API 密钥将无法工作。
                            </p>
                             <a 
                                href="https://ai.google.dev/gemini-api/docs/billing" 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs font-bold text-cyan-600 dark:text-cyan-400 hover:underline mt-1"
                            >
                                查看计费文档 <ExternalLink className="w-3 h-3" />
                            </a>
                         </div>
                    </div>
                </div>

                <button 
                    onClick={handleSelectKey}
                    className="w-full py-3.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl font-bold shadow-lg shadow-amber-500/20 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2"
                >
                    <Key className="w-4 h-4" />
                    <span>选择付费 API 密钥</span>
                </button>
            </div>
        </div>
    </div>
  );

  return (
    <>
    {/* Block usage if key is missing */}
    {!checkingKey && !hasApiKey && <KeySelectionModal />}

    {showIntro ? (
      <IntroScreen onComplete={() => setShowIntro(false)} />
    ) : (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-200 font-sans selection:bg-cyan-500 selection:text-white pb-20 relative overflow-x-hidden animate-in fade-in duration-1000 transition-colors">
      
      {/* Background Elements */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-100 via-slate-50 to-white dark:from-indigo-900 dark:via-slate-950 dark:to-black z-0 transition-colors"></div>
      <div className="fixed inset-0 opacity-5 dark:opacity-20 z-0 pointer-events-none" style={{
          backgroundImage: `radial-gradient(currentColor 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
      }}></div>

      {/* Navbar */}
      <header className="border-b border-slate-200 dark:border-white/10 sticky top-0 z-50 backdrop-blur-md bg-white/70 dark:bg-slate-950/60 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 md:h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 md:gap-4 group cursor-pointer" onClick={resetApp}>
            <div className="relative scale-90 md:scale-100">
                <div className="absolute inset-0 bg-cyan-500 blur-lg opacity-20 dark:opacity-40 group-hover:opacity-60 transition-opacity"></div>
                <div className="bg-white dark:bg-gradient-to-br dark:from-slate-900 dark:to-slate-800 p-2.5 rounded-xl border border-slate-200 dark:border-white/10 relative z-10 shadow-sm dark:shadow-none">
                   <PresentationIcon className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
                </div>
            </div>
            <div className="flex flex-col">
                <span className="font-display font-bold text-lg md:text-2xl tracking-tight text-slate-900 dark:text-white leading-none">
                SlideGenius <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-indigo-600 dark:from-cyan-400 dark:to-amber-400">AI</span>
                </span>
                <span className="text-[8px] md:text-[10px] uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400 font-medium">文本转演示文稿</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
              <button 
                onClick={handleSelectKey}
                className="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-cyan-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs font-medium transition-colors border border-slate-200 dark:border-white/10"
                title="切换 API 密钥"
              >
                <Key className="w-3.5 h-3.5" />
                <span>API 密钥</span>
              </button>

              <button 
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-2 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-300 transition-colors border border-slate-200 dark:border-white/10 shadow-sm"
              >
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
          </div>
        </div>
      </header>

      <main className="px-3 sm:px-6 py-4 md:py-8 relative z-10">
        
        <div className={`max-w-5xl mx-auto transition-all duration-500 ${presentation ? 'mb-4' : 'min-h-[70vh] flex flex-col justify-center'}`}>
          
          {!presentation && !isLoading && (
            <div className="text-center mb-6 md:mb-12 space-y-4 animate-in slide-in-from-bottom-8 duration-700 fade-in">
              <h1 className="text-3xl sm:text-5xl md:text-7xl font-display font-bold text-slate-900 dark:text-white tracking-tight leading-tight">
                将文章一键转化为 <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 via-indigo-600 to-purple-600 dark:from-cyan-400 dark:via-indigo-400 dark:to-purple-400">精美演示文稿</span>
              </h1>
              <p className="text-sm md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto font-light leading-relaxed">
                粘贴文本，选择风格，即刻获得专业 PPT。支持 PDF/Word 上传。
              </p>
            </div>
          )}

          {/* Input Form */}
          <form onSubmit={handleGenerate} className={`relative z-20 transition-all duration-500 ${isLoading ? 'opacity-50 pointer-events-none scale-95 blur-sm' : 'scale-100'} ${presentation ? 'hidden' : ''}`}>
            
            <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-amber-500 rounded-3xl opacity-10 dark:opacity-20 group-hover:opacity-30 dark:group-hover:opacity-40 transition duration-500 blur-xl"></div>
                
                <div className="relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 p-2 rounded-3xl shadow-2xl">
                    
                    {/* Main Text Area */}
                    <div className="relative">
                        <div className="absolute top-4 left-4 p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-400">
                             <FileText className="w-5 h-5" />
                        </div>
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            placeholder="请在此输入主题提示词，粘贴文章内容，或上传文件..."
                            className="w-full min-h-[150px] pl-16 pr-6 py-5 bg-transparent border-none outline-none text-base md:text-lg placeholder:text-slate-400 font-medium text-slate-900 dark:text-white resize-none"
                        />
                        
                        {/* File Upload Button inside Text Area */}
                        <div className="absolute bottom-4 left-4">
                            <input 
                                type="file" 
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                accept=".pdf,.docx,.txt"
                                className="hidden"
                            />
                            <button 
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs font-bold transition-colors border border-slate-200 dark:border-white/10"
                            >
                                <Paperclip className="w-3.5 h-3.5" />
                                <span>上传文件 (PDF, DOCX, TXT)</span>
                            </button>
                        </div>

                        {/* Attached File Indicator */}
                        {uploadedFile && (
                            <div className="absolute bottom-4 left-48 animate-in fade-in zoom-in duration-300">
                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 text-xs font-bold border border-cyan-200 dark:border-cyan-500/30">
                                    <FileIcon className="w-3.5 h-3.5" />
                                    <span className="max-w-[150px] truncate">{uploadedFile.name}</span>
                                    <button 
                                        type="button" 
                                        onClick={removeFile}
                                        className="ml-1 p-0.5 hover:bg-cyan-200 dark:hover:bg-cyan-800 rounded-full"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Controls Bar */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 p-2 mt-2 border-t border-slate-100 dark:border-white/5 pt-4">
                    
                    {/* Level Selector */}
                    <div className="bg-slate-50 dark:bg-slate-950/50 rounded-xl border border-slate-200 dark:border-white/5 px-3 py-2 flex items-center gap-2 relative overflow-hidden">
                        <GraduationCap className="w-4 h-4 text-cyan-600 dark:text-cyan-400 flex-shrink-0" />
                        <div className="flex flex-col w-full min-w-0">
                            <label className="text-[9px] font-bold text-slate-400 uppercase">语气</label>
                            <select 
                                value={complexityLevel} 
                                onChange={(e) => setComplexityLevel(e.target.value as ComplexityLevel)}
                                className="bg-transparent border-none text-xs md:text-sm font-bold text-slate-900 dark:text-white focus:ring-0 cursor-pointer p-0 w-full"
                            >
                                <option>通用</option>
                                <option>专业</option>
                                <option>学术</option>
                                <option>行政高管</option>
                            </select>
                        </div>
                    </div>

                    {/* Style Selector */}
                    <div className="bg-slate-50 dark:bg-slate-950/50 rounded-xl border border-slate-200 dark:border-white/5 px-3 py-2 flex items-center gap-2 relative overflow-hidden">
                         <Palette className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0" />
                        <div className="flex flex-col w-full min-w-0">
                            <label className="text-[9px] font-bold text-slate-400 uppercase">风格</label>
                            <select 
                                value={visualStyle} 
                                onChange={(e) => setVisualStyle(e.target.value as VisualStyle)}
                                className="bg-transparent border-none text-xs md:text-sm font-bold text-slate-900 dark:text-white focus:ring-0 cursor-pointer p-0 w-full"
                            >
                                <option>现代简约</option>
                                <option>商务科技</option>
                                <option>创意艺术</option>
                                <option>深色模式</option>
                                <option>自然清新</option>
                            </select>
                        </div>
                    </div>

                     {/* Language Selector */}
                     <div className="bg-slate-50 dark:bg-slate-950/50 rounded-xl border border-slate-200 dark:border-white/5 px-3 py-2 flex items-center gap-2 relative overflow-hidden">
                         <Globe className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                        <div className="flex flex-col w-full min-w-0">
                            <label className="text-[9px] font-bold text-slate-400 uppercase">语言</label>
                            <select 
                                value={language} 
                                onChange={(e) => setLanguage(e.target.value as Language)}
                                className="bg-transparent border-none text-xs md:text-sm font-bold text-slate-900 dark:text-white focus:ring-0 cursor-pointer p-0 w-full"
                            >
                                <option>简体中文</option>
                                <option>English</option>
                                <option>Spanish</option>
                                <option>French</option>
                                <option>German</option>
                                <option>Japanese</option>
                            </select>
                        </div>
                    </div>

                     {/* Slide Count Selector */}
                     <div className="bg-slate-50 dark:bg-slate-950/50 rounded-xl border border-slate-200 dark:border-white/5 px-3 py-2 flex items-center gap-2 relative overflow-hidden">
                         <Layers className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                        <div className="flex flex-col w-full min-w-0">
                            <label className="text-[9px] font-bold text-slate-400 uppercase">页数: {slideCount}</label>
                            <input 
                                type="range"
                                min="3"
                                max="12"
                                step="1"
                                value={slideCount}
                                onChange={(e) => setSlideCount(parseInt(e.target.value))}
                                className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700 accent-amber-500"
                            />
                        </div>
                    </div>

                    {/* Generate Button */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="col-span-2 md:col-span-1 h-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:brightness-110 transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>生成</span>
                    </button>

                    </div>
                </div>
            </div>
          </form>
        </div>

        {isLoading && <Loading status={loadingMessage} step={loadingStep} />}

        {error && (
          <div className="max-w-2xl mx-auto mt-8 p-6 bg-red-100 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl flex items-center gap-4 text-red-800 dark:text-red-200 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-4 shadow-sm">
            <AlertCircle className="w-6 h-6 flex-shrink-0 text-red-500 dark:text-red-400" />
            <div className="flex-1">
                <p className="font-medium">{error}</p>
                {(error.includes("访问被拒绝") || error.includes("计费")) && (
                    <button 
                        onClick={handleSelectKey}
                        className="mt-2 text-xs font-bold text-red-700 dark:text-red-300 underline hover:text-red-900 dark:hover:text-red-100"
                    >
                        选择其他 API 密钥
                    </button>
                )}
            </div>
          </div>
        )}

        {presentation && !isLoading && (
            <>
                <SlideViewer 
                    presentation={presentation} 
                    onReset={resetApp}
                />
                {presentation.sources.length > 0 && <SearchResults results={presentation.sources} />}
                
                <div className="flex justify-center mt-12 pb-12">
                    <button 
                        onClick={resetApp}
                        className="px-6 py-3 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-full font-bold hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors shadow-lg"
                    >
                        创建新演示文稿
                    </button>
                </div>
            </>
        )}

      </main>
    </div>
    )}
    </>
  );
};

export default App;