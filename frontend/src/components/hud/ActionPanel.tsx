import { CoreState, PendingAction, SystemStats, TimelineEntry } from '../../types/events';
import { ToolStatus } from '../../store/agentStore';


interface ActionPanelProps {
  state: CoreState;
  activeTool: { name: string; args: Record<string, any> } | null;
  pendingAction: PendingAction | null;
  stats: SystemStats | null;
  tools: Record<string, ToolStatus>;
  timeline: TimelineEntry[];
}

export function ActionPanel({ stats, tools, timeline }: ActionPanelProps) {
  const toolList = Object.values(tools);

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden pointer-events-auto">
      
      {/* 1. TOP TOOLS LIST PANEL */}
      <div className="flex-1 rounded-2xl bg-[#090514]/60 border border-[#a855f7]/25 backdrop-blur-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-[0_0_20px_rgba(139,92,246,0.1)]">
        <div className="flex items-center justify-between text-xs font-mono text-[#d8b4fe] font-medium border-b border-slate-800/40 pb-2">
          <div className="flex items-center gap-2">
            <span>🛠️</span>
            <span className="tracking-wider uppercase">TOOLS</span>
          </div>
          <span className="text-[10px] text-slate-500">{toolList.length} REGISTERED</span>
        </div>

        {/* Tools List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 my-2 pr-1 font-mono text-[10.5px]">
          {toolList.map((tool, idx) => (
            <div key={idx} className="flex items-center justify-between bg-[#120a26]/70 border border-[#a855f7]/20 p-2 rounded-xl">
              <div className="flex items-center gap-2.5">
                <span className="text-sm">{tool.icon}</span>
                <div className="flex flex-col">
                  <span className="font-bold text-slate-200 text-[10px]">{tool.name}</span>
                  <span className="text-[9px] text-slate-500">{tool.desc}</span>
                </div>
              </div>
              <span className={`text-[8.5px] px-1.5 py-0.5 rounded font-bold ${
                tool.status === 'ACTIVE' ? 'text-purple-300 bg-purple-500/20 border border-purple-500/30 animate-pulse' :
                tool.status === 'SUCCESS' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' :
                tool.status === 'ERROR' ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' :
                'text-slate-500 bg-slate-800/40'
              }`}>
                {tool.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. MIDDLE SYSTEM METRICS PANEL */}
      <div className="h-44 rounded-2xl bg-[#090514]/60 border border-[#a855f7]/25 backdrop-blur-xl p-3.5 flex flex-col justify-between shadow-[0_0_20px_rgba(139,92,246,0.1)]">
        <div className="flex items-center gap-2 text-xs font-mono text-[#d8b4fe] font-medium border-b border-slate-800/40 pb-1.5">
          <span>📊</span>
          <span className="tracking-wider uppercase">SYSTEM METRICS</span>
        </div>

        {/* Live Gauges */}
        <div className="grid grid-cols-3 gap-2 font-mono text-[10px]">
          <div>
            <div className="text-slate-500">CPU</div>
            <div className="text-slate-100 font-bold text-xs">{stats ? `${stats.cpu.usage.toFixed(0)}%` : 'N/A'}</div>
            <div className="h-1 bg-[#1a0f35] rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-emerald-400 transition-all duration-500" style={{ width: stats ? `${stats.cpu.usage}%` : '0%' }} />
            </div>
          </div>
          <div>
            <div className="text-slate-500">RAM</div>
            <div className="text-slate-100 font-bold text-xs">{stats ? `${stats.ram.used_gb} GB` : 'N/A'}</div>
            <div className="h-1 bg-[#1a0f35] rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-cyan-400 transition-all duration-500" style={{ width: stats ? `${stats.ram.usage}%` : '0%' }} />
            </div>
          </div>
          <div>
            <div className="text-slate-500">NET</div>
            <div className="text-slate-100 font-bold text-xs">N/A</div>
            <div className="h-1 bg-[#1a0f35] rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-amber-400 w-0" />
            </div>
          </div>
        </div>

        {/* Telemetry Footer Row */}
        <div className="grid grid-cols-3 gap-2 font-mono text-[9px] border-t border-slate-800/40 pt-2">
          <div>
            <div className="text-slate-500">TOKENS</div>
            <div className="text-slate-200 font-bold">N/A</div>
          </div>
          <div>
            <div className="text-slate-500">LATENCY</div>
            <div className="text-slate-200 font-bold">N/A</div>
          </div>
          <div>
            <div className="text-slate-500">UPTIME</div>
            <div className="text-slate-200 font-bold">N/A</div>
          </div>
        </div>
      </div>

      {/* 3. BOTTOM RECENT ACTIVITY PANEL */}
      <div className="h-44 rounded-2xl bg-[#090514]/60 border border-[#a855f7]/25 backdrop-blur-xl p-3.5 flex flex-col justify-between shadow-[0_0_20px_rgba(139,92,246,0.1)]">
        <div className="flex items-center gap-2 text-xs font-mono text-[#d8b4fe] font-medium border-b border-slate-800/40 pb-1.5">
          <span>📋</span>
          <span className="tracking-wider uppercase">RECENT ACTIVITY</span>
        </div>

        <div className="overflow-y-auto space-y-1.5 font-mono text-[10px]">
          {timeline.length === 0 ? (
            <div className="text-slate-600 italic text-[9.5px]">No recent agent activity recorded...</div>
          ) : (
            timeline.slice(-6).reverse().map((item) => (
              <div key={item.id} className="flex items-center justify-between text-slate-300">
                <span className="text-slate-500 text-[9px]">{item.time}</span>
                <span className="truncate mx-2 flex-1 text-right text-slate-300">{item.label}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${item.error ? 'bg-rose-500' : item.check ? 'bg-emerald-400' : 'bg-[#a855f7]'}`} />
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}


