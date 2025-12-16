import React, { useState } from 'react';
import { suggestUIUX } from '../services/geminiService';
import { Palette, Sparkles, LayoutTemplate, Loader2, Globe, ArrowRight, Code } from 'lucide-react';

export const UXDesigner: React.FC = () => {
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [suggestions, setSuggestions] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatePrototype, setGeneratePrototype] = useState(false);

  const handleSuggest = async () => {
    if (!description.trim() && !url.trim()) return;
    setLoading(true);
    setSuggestions('');
    try {
      const result = await suggestUIUX(description, url, generatePrototype);
      setSuggestions(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 h-full">
      <div className="flex flex-col justify-center space-y-10">
        <div>
          <h2 className="text-4xl font-bold text-white mb-4 flex items-center gap-4 tracking-tighter uppercase">
            <Palette className="text-white" strokeWidth={1} size={32} /> UI/UX Designer
          </h2>
          <p className="text-neutral-400 font-light max-w-lg border-l border-white/20 pl-4">
            Generative interface design engine. Combine live site analysis with your creative vision to generate bespoke architectural recommendations or full-scale prototypes.
          </p>
        </div>

        <div className="bg-neutral-950 p-8 border border-neutral-900 space-y-8">
          
          <div className="space-y-4">
             <div className="flex flex-col space-y-2">
                <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Target Website (Optional)</label>
                <div className="flex items-center border-b border-neutral-800 py-2 focus-within:border-white transition-colors">
                  <Globe className="text-neutral-400 mr-4" size={20} />
                  <input 
                    type="url" 
                    className="bg-transparent border-none outline-none text-white w-full placeholder:text-neutral-700 font-mono text-sm uppercase"
                    placeholder="HTTPS://EXAMPLE.COM"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>
             </div>

             <div className="flex flex-col space-y-2">
                <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Vision / Requirements</label>
                <div className="bg-black border border-neutral-800 p-4 focus-within:border-white transition-colors">
                    <textarea
                      className="w-full h-32 bg-transparent text-white resize-none outline-none placeholder:text-neutral-700 text-sm font-light leading-relaxed"
                      placeholder="Describe your aesthetic goals, user persona, or specific problems to solve..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
             </div>

             {/* Prototype Toggle */}
             <div 
               className="flex items-center gap-3 cursor-pointer group"
               onClick={() => setGeneratePrototype(!generatePrototype)}
             >
                <div className={`w-5 h-5 border flex items-center justify-center transition-colors ${generatePrototype ? 'bg-white border-white' : 'border-neutral-700 group-hover:border-neutral-500'}`}>
                   {generatePrototype && <div className="w-2 h-2 bg-black" />}
                </div>
                <span className={`text-xs font-bold uppercase tracking-widest transition-colors ${generatePrototype ? 'text-white' : 'text-neutral-500 group-hover:text-neutral-300'}`}>
                  Auto-Generate Prototype Code
                </span>
             </div>
          </div>
          
          <button
            onClick={handleSuggest}
            disabled={loading || (!description && !url)}
            className="w-full bg-transparent border border-white text-white hover:bg-white hover:text-black py-4 font-bold uppercase tracking-[0.15em] text-xs flex items-center justify-center gap-3 transition-all duration-300 disabled:opacity-50 disabled:border-neutral-800 disabled:text-neutral-800 disabled:hover:bg-transparent"
          >
            {loading ? <Loader2 className="animate-spin" size={16} /> : (generatePrototype ? "Construct UI Matrix" : "Generate Analysis")}
            {!loading && <ArrowRight size={16} />}
          </button>
        </div>
      </div>

      <div className="relative bg-[#050505] border border-[#1a1a1a] p-12 min-h-[600px] flex flex-col shadow-2xl">
         <div className="absolute top-0 right-0 p-6 opacity-20">
            {generatePrototype ? <Code size={48} className="text-white" strokeWidth={0.5} /> : <LayoutTemplate size={48} className="text-white" strokeWidth={0.5} />}
         </div>

         {!suggestions && !loading && (
           <div className="flex-1 flex flex-col items-center justify-center text-neutral-600">
             <div className="w-16 h-16 border border-neutral-800 rounded-full flex items-center justify-center mb-6">
                <Sparkles size={24} strokeWidth={1} />
             </div>
             <span className="text-xs font-bold uppercase tracking-[0.3em]">Awaiting Input</span>
             <div className="w-12 h-px bg-neutral-800 mt-6"></div>
           </div>
         )}

         {loading && (
           <div className="flex-1 flex flex-col items-center justify-center relative z-10">
             <div className="w-12 h-12 border border-white border-b-transparent rounded-full animate-spin mb-8"></div>
             <p className="text-neutral-400 font-mono text-[10px] uppercase tracking-[0.3em] animate-pulse">
               {generatePrototype ? 'Synthesizing_React_Components...' : 'Rendering_Design_Matrix...'}
             </p>
           </div>
         )}

         {suggestions && (
           <div className="flex-1 overflow-y-auto custom-scrollbar relative z-10 pr-4">
             <h3 className="text-2xl font-light text-white mb-8 border-b border-neutral-800 pb-6 tracking-wide">
                {generatePrototype ? 'Prototype' : 'Design'} <span className="font-bold">Matrix</span>
             </h3>
             <div className="prose prose-invert prose-p:text-[#a3a3a3] prose-headings:text-white prose-li:text-[#a3a3a3] prose-strong:text-white prose-a:text-white prose-a:underline prose-blockquote:border-l-white prose-blockquote:text-neutral-400 prose-pre:bg-neutral-900 prose-pre:border prose-pre:border-neutral-800">
                <div className="whitespace-pre-wrap font-sans text-sm leading-8 font-light">
                  {suggestions}
                </div>
             </div>
           </div>
         )}
      </div>
    </div>
  );
};