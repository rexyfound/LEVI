import { CoreState, SystemStats } from '../../types/events';


interface TopHeaderProps {
  state: CoreState;
  provider: string;
  stats: SystemStats | null;
  isOnline: boolean;
}

export function TopHeader({ isOnline }: TopHeaderProps) {
  const dateStr = new Date().toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <header className="w-full h-12 rounded-xl bg-[#090514]/70 border border-[#a855f7]/25 backdrop-blur-xl px-4 flex items-center justify-between text-xs font-mono z-20 pointer-events-auto shadow-[0_0_20px_rgba(139,92,246,0.1)]">
      {/* Left Brand Identifier */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-[#180e30] border border-[#a855f7]/40 flex items-center justify-center text-[#d8b4fe]">
          ⚛️
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-slate-100 text-[11px] tracking-wider">LEVI OS</span>
          <span className="text-[9px] text-slate-500">v0.1.0-alpha</span>
        </div>
      </div>

      {/* Center Main Title */}
      <div className="flex flex-col items-center">
        <span className="text-sm font-bold text-[#d8b4fe] tracking-[0.25em]">L E V I</span>
        <span className="text-[9px] text-slate-500 tracking-wider">ADAPTIVE INTELLIGENCE SYSTEM</span>
      </div>

      {/* Right Clock & System Status */}
      <div className="flex items-center gap-4">
        <div className="flex flex-col items-end text-[10px] text-slate-400">
          <span className="font-bold text-slate-200">{timeStr}</span>
          <span className="text-[8.5px] text-slate-500">{dateStr}</span>
        </div>

        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] border ${
          isOnline ? 'bg-[#0d1f18] border-emerald-500/30 text-emerald-400' : 'bg-rose-950/30 border-rose-500/30 text-rose-400'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className="font-semibold">SYSTEM STATUS</span>
          <span className="text-[9px] font-normal">{isOnline ? 'OPTIMAL' : 'OFFLINE'}</span>
        </div>
      </div>
    </header>
  );
}
