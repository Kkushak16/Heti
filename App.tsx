import React, { useState } from 'react';
import { AppMode } from './types';
import { Modernizer } from './components/Modernizer';
import { Auditor } from './components/Auditor';
import { UXDesigner } from './components/UXDesigner';
import { GrowthStrategist } from './components/GrowthStrategist';
import { Terminal, Shield, PenTool, BarChart3, Menu, X, Box, ArrowRight } from 'lucide-react';

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>(AppMode.LANDING);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const NavItem = ({ m, icon: Icon, label }: { m: AppMode; icon: any; label: string }) => (
    <button
      onClick={() => {
        setMode(m);
        setIsMobileMenuOpen(false);
      }}
      className={`flex items-center gap-4 px-4 py-3 rounded-none w-full transition-all duration-300 border-l-2 ${
        mode === m 
          ? 'border-white text-white bg-neutral-900' 
          : 'border-transparent text-neutral-400 hover:text-white hover:bg-neutral-900/50'
      }`}
    >
      <Icon size={18} strokeWidth={1.5} />
      <span className="font-medium tracking-widest text-sm uppercase">{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-black text-neutral-200 flex flex-col md:flex-row font-sans selection:bg-white selection:text-black">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-6 bg-black border-b border-neutral-800 z-50 relative">
        <div className="flex items-center gap-2 font-bold text-xl text-white tracking-widest uppercase">
          <Box className="text-white" /> Heti
        </div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-white">
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <div className={`
        fixed inset-0 z-40 bg-black transform transition-transform duration-500 md:relative md:translate-x-0 md:bg-black md:w-80 md:border-r md:border-neutral-900 flex flex-col
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-10 hidden md:flex flex-col gap-6 mb-2">
           <div className="w-12 h-12 bg-white text-black flex items-center justify-center">
             <Box size={24} strokeWidth={2} />
           </div>
           <h1 className="text-4xl font-bold text-white tracking-tighter">HETI.</h1>
        </div>

        <nav className="flex-1 px-0 space-y-1 py-6">
          <NavItem m={AppMode.LANDING} icon={Box} label="Overview" />
          <div className="pt-8 pb-4 px-6 text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">Engines</div>
          <NavItem m={AppMode.MODERNIZE} icon={Terminal} label="Modernizer" />
          <NavItem m={AppMode.AUDIT} icon={Shield} label="Auditor" />
          <NavItem m={AppMode.DESIGN} icon={PenTool} label="Designer" />
          <NavItem m={AppMode.GROWTH} icon={BarChart3} label="Strategist" />
        </nav>

        <div className="p-8 border-t border-neutral-900">
           <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
              SYSTEM STATUS: ONLINE
           </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 h-[calc(100vh-80px)] md:h-screen overflow-y-auto bg-black relative">
        <div className="container mx-auto p-6 md:p-12 relative z-10 max-w-7xl">
          {mode === AppMode.LANDING && (
            <div className="flex flex-col justify-center min-h-[70vh] space-y-12 animate-in fade-in duration-1000">
              <div className="border-b border-neutral-800 pb-12">
                 <h1 className="text-7xl md:text-9xl font-bold tracking-tighter text-white mb-6">
                   ELEVATE<br/>
                   <span className="text-neutral-500">THE CODE.</span>
                 </h1>
                 <p className="text-xl md:text-2xl text-neutral-300 max-w-3xl font-light leading-relaxed">
                   Advanced architectural reconstruction and analysis. 
                   Transform legacy systems into high-performance modern frameworks.
                 </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-neutral-900 border border-neutral-900">
                 <button onClick={() => setMode(AppMode.MODERNIZE)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <Terminal className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Modernizer</h3>
                      <p className="text-neutral-400 text-sm">Refactor Legacy to React/TS</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.AUDIT)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <Shield className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Auditor</h3>
                      <p className="text-neutral-400 text-sm">Security & Flaw Detection</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.DESIGN)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <PenTool className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Designer</h3>
                      <p className="text-neutral-400 text-sm">UI/UX Architecture</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.GROWTH)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <BarChart3 className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Strategist</h3>
                      <p className="text-neutral-400 text-sm">Growth & Reach Analysis</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
              </div>
            </div>
          )}

          {mode === AppMode.MODERNIZE && <Modernizer />}
          {mode === AppMode.AUDIT && <Auditor />}
          {mode === AppMode.DESIGN && <UXDesigner />}
          {mode === AppMode.GROWTH && <GrowthStrategist />}
        </div>
      </main>
    </div>
  );
};

export default App;import React, { useState } from 'react';
import { AppMode } from './types';
import { Modernizer } from './components/Modernizer';
import { Auditor } from './components/Auditor';
import { UXDesigner } from './components/UXDesigner';
import { GrowthStrategist } from './components/GrowthStrategist';
import { Terminal, Shield, PenTool, BarChart3, Menu, X, Box, ArrowRight } from 'lucide-react';

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>(AppMode.LANDING);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const NavItem = ({ m, icon: Icon, label }: { m: AppMode; icon: any; label: string }) => (
    <button
      onClick={() => {
        setMode(m);
        setIsMobileMenuOpen(false);
      }}
      className={`flex items-center gap-4 px-4 py-3 rounded-none w-full transition-all duration-300 border-l-2 ${
        mode === m 
          ? 'border-white text-white bg-neutral-900' 
          : 'border-transparent text-neutral-400 hover:text-white hover:bg-neutral-900/50'
      }`}
    >
      <Icon size={18} strokeWidth={1.5} />
      <span className="font-medium tracking-widest text-sm uppercase">{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-black text-neutral-200 flex flex-col md:flex-row font-sans selection:bg-white selection:text-black">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-6 bg-black border-b border-neutral-800 z-50 relative">
        <div className="flex items-center gap-2 font-bold text-xl text-white tracking-widest uppercase">
          <Box className="text-white" /> Heti
        </div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-white">
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <div className={`
        fixed inset-0 z-40 bg-black transform transition-transform duration-500 md:relative md:translate-x-0 md:bg-black md:w-80 md:border-r md:border-neutral-900 flex flex-col
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-10 hidden md:flex flex-col gap-6 mb-2">
           <div className="w-12 h-12 bg-white text-black flex items-center justify-center">
             <Box size={24} strokeWidth={2} />
           </div>
           <h1 className="text-4xl font-bold text-white tracking-tighter">HETI.</h1>
        </div>

        <nav className="flex-1 px-0 space-y-1 py-6">
          <NavItem m={AppMode.LANDING} icon={Box} label="Overview" />
          <div className="pt-8 pb-4 px-6 text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">Engines</div>
          <NavItem m={AppMode.MODERNIZE} icon={Terminal} label="Modernizer" />
          <NavItem m={AppMode.AUDIT} icon={Shield} label="Auditor" />
          <NavItem m={AppMode.DESIGN} icon={PenTool} label="Designer" />
          <NavItem m={AppMode.GROWTH} icon={BarChart3} label="Strategist" />
        </nav>

        <div className="p-8 border-t border-neutral-900">
           <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
              SYSTEM STATUS: ONLINE
           </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 h-[calc(100vh-80px)] md:h-screen overflow-y-auto bg-black relative">
        <div className="container mx-auto p-6 md:p-12 relative z-10 max-w-7xl">
          {mode === AppMode.LANDING && (
            <div className="flex flex-col justify-center min-h-[70vh] space-y-12 animate-in fade-in duration-1000">
              <div className="border-b border-neutral-800 pb-12">
                 <h1 className="text-7xl md:text-9xl font-bold tracking-tighter text-white mb-6">
                   ELEVATE<br/>
                   <span className="text-neutral-500">THE CODE.</span>
                 </h1>
                 <p className="text-xl md:text-2xl text-neutral-300 max-w-3xl font-light leading-relaxed">
                   Advanced architectural reconstruction and analysis. 
                   Transform legacy systems into high-performance modern frameworks.
                 </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-neutral-900 border border-neutral-900">
                 <button onClick={() => setMode(AppMode.MODERNIZE)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <Terminal className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Modernizer</h3>
                      <p className="text-neutral-400 text-sm">Refactor Legacy to React/TS</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.AUDIT)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <Shield className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Auditor</h3>
                      <p className="text-neutral-400 text-sm">Security & Flaw Detection</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.DESIGN)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <PenTool className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Designer</h3>
                      <p className="text-neutral-400 text-sm">UI/UX Architecture</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
                 <button onClick={() => setMode(AppMode.GROWTH)} className="group relative bg-black p-10 hover:bg-neutral-900 transition-colors text-left h-64 flex flex-col justify-between">
                    <BarChart3 className="w-8 h-8 text-neutral-400 group-hover:text-white transition-colors" />
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2 uppercase tracking-wide">Strategist</h3>
                      <p className="text-neutral-400 text-sm">Growth & Reach Analysis</p>
                    </div>
                    <ArrowRight className="absolute top-10 right-10 text-neutral-600 group-hover:text-white -rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                 </button>
              </div>
            </div>
          )}

          {mode === AppMode.MODERNIZE && <Modernizer />}
          {mode === AppMode.AUDIT && <Auditor />}
          {mode === AppMode.DESIGN && <UXDesigner />}
          {mode === AppMode.GROWTH && <GrowthStrategist />}
        </div>
      </main>
    </div>
  );
};

export default App;