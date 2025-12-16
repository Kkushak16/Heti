import React, { useState } from 'react';
import { auditWebsite } from '../services/geminiService';
import { ShieldAlert, CheckCircle, AlertTriangle, Search, Loader2, Globe, FileText } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

export const Auditor: React.FC = () => {
  const [inputType, setInputType] = useState<'text' | 'url'>('text');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<{ markdown: string; score: number } | null>(null);

  const handleAudit = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setReport(null);
    try {
      const result = await auditWebsite(content, inputType === 'url');
      setReport(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#ffffff'; // White for good
    if (score >= 50) return '#a3a3a3'; // Grey for warning
    return '#525252'; // Dark Grey for danger
  };

  const chartData = report ? [
    { name: 'Health', value: report.score },
    { name: 'Defects', value: 100 - report.score },
  ] : [];

  return (
    <div className="space-y-12">
      <div className="border-b border-neutral-900 pb-8">
        <h2 className="text-4xl font-bold text-white mb-4 tracking-tighter uppercase">Security Auditor</h2>
        <p className="text-neutral-400 max-w-2xl font-light">
          Diagnostic scan for vulnerabilities (SQLi, XSS), logic flaws, and performance bottlenecks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Input Column */}
        <div className="lg:col-span-1 space-y-6">
           <div className="flex border-b border-neutral-800">
              <button 
                onClick={() => setInputType('text')}
                className={`flex-1 pb-4 text-xs font-bold uppercase tracking-[0.2em] transition-all ${inputType === 'text' ? 'text-white border-b-2 border-white' : 'text-neutral-400 hover:text-neutral-300'}`}
              >
                Manual Entry
              </button>
              <button 
                onClick={() => setInputType('url')}
                className={`flex-1 pb-4 text-xs font-bold uppercase tracking-[0.2em] transition-all ${inputType === 'url' ? 'text-white border-b-2 border-white' : 'text-neutral-400 hover:text-neutral-300'}`}
              >
                Remote Target
              </button>
           </div>

          <div className="h-96">
            {inputType === 'text' ? (
              <textarea
                className="w-full h-full bg-neutral-950 text-neutral-200 p-6 border border-neutral-900 focus:outline-none resize-none text-xs font-mono uppercase focus:border-white transition-colors placeholder:text-neutral-600"
                placeholder="PASTE SYSTEM ARCHITECTURE OR CODE..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            ) : (
               <div className="w-full h-full bg-neutral-950 border border-neutral-900 p-8 flex flex-col items-center justify-center">
                  <div className="w-full">
                    <label className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4 block">Target URI</label>
                    <div className="flex items-center bg-black border border-neutral-800 px-4 py-4 focus-within:border-white transition-colors">
                      <Globe className="text-white mr-4" size={18} />
                      <input 
                        type="url" 
                        className="bg-transparent border-none outline-none text-white w-full placeholder:text-neutral-600 font-mono text-sm uppercase"
                        placeholder="HTTPS://"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                      />
                    </div>
                  </div>
               </div>
            )}
          </div>
          <button
            onClick={handleAudit}
            disabled={loading || !content}
            className="w-full bg-white hover:bg-neutral-200 disabled:opacity-50 text-black py-5 font-bold text-sm uppercase tracking-[0.2em] flex justify-center items-center gap-3 transition-all"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Execute Scan"}
          </button>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2 bg-neutral-950 border border-neutral-900 min-h-[500px] flex flex-col relative">
          {!report && !loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-neutral-600">
              <ShieldAlert size={80} strokeWidth={0.5} />
              <p className="tracking-[0.5em] uppercase text-xs font-bold mt-6">System Standby</p>
            </div>
          )}

          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50 backdrop-blur-sm z-10">
               <div className="w-16 h-16 border-2 border-white border-t-transparent rounded-full animate-spin mb-6"></div>
               <p className="text-white font-mono tracking-[0.2em] text-xs uppercase animate-pulse">Diagnostic_In_Progress...</p>
            </div>
          )}

          {report && (
            <div className="p-10 h-full flex flex-col">
              <div className="flex items-start justify-between mb-10 border-b border-neutral-900 pb-8">
                 <div>
                   <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Audit Report</h3>
                   <p className="text-neutral-400 text-xs font-mono">ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}</p>
                 </div>
                 <div className="flex items-center gap-8">
                    <div className="text-right">
                      <div className="text-5xl font-bold tracking-tighter text-white">
                        {report.score}
                      </div>
                      <div className="text-[10px] text-neutral-400 uppercase tracking-[0.2em] font-bold mt-1">Integrity Score</div>
                    </div>
                    <div className="w-20 h-20 grayscale opacity-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={25}
                            outerRadius={38}
                            paddingAngle={5}
                            dataKey="value"
                            startAngle={90}
                            endAngle={-270}
                            stroke="none"
                          >
                            <Cell key="health" fill="#ffffff" />
                            <Cell key="defects" fill="#262626" />
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                 </div>
              </div>

              <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar">
                 <div className="prose prose-invert prose-sm max-w-none">
                    <div className="whitespace-pre-wrap font-sans text-neutral-300 font-light leading-7">
                      {report.markdown.split('\n').map((line, i) => (
                         <div key={i} className="mb-2">{line}</div>
                      ))}
                    </div>
                 </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};