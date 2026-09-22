import { CoreState } from '../../types/events';


interface HistoryConsoleProps {
  state: CoreState;
  provider: string;
  model?: string;
  isOnline: boolean;
}

export function HistoryConsole({ provider, model, isOnline }: HistoryConsoleProps) {
  return (
    <footer className="h-8 rounded-xl bg-[#090514]/80 border border-[#a855f7]/25 backdrop-blur-xl px-4 flex items-center justify-between font-mono text-[10px] text-slate-400 z-10 pointer-events-auto shadow-[0_0_15px_rgba(139,92,246,0.1)]">
      
      {/* LEFT STATUS ITEMS */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 uppercase">MODEL:</span>
          <span className="text-slate-200 font-bold">{model && model !== 'N/A' ? model : 'AUTO ROUTER'}</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 uppercase">PROVIDER:</span>
          <span className="text-[#c084fc] font-bold uppercase">{provider}</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 uppercase">MODE:</span>
          <span className="text-slate-300 font-semibold">ADAPTIVE AGENT</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 uppercase">VOICE:</span>
          <span className="text-slate-300">ACTIVE</span>
          <div className="flex items-center gap-0.5 ml-1">
            <span className="w-0.5 h-2 bg-[#a855f7] animate-pulse" />
            <span className="w-0.5 h-3 bg-[#c084fc] animate-pulse" />
            <span className="w-0.5 h-1.5 bg-[#a855f7] animate-pulse" />
          </div>
        </div>
      </div>

      {/* RIGHT CONNECTION BADGE */}
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-rose-500'}`} />
        <span className={`font-bold ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isOnline ? 'CONNECTED (WS /ws/agent)' : 'DISCONNECTED'}
        </span>
      </div>

    </footer>
  );
}
