import { useState } from 'react';
import { CoreState } from '../../types/events';


interface ThinkingPanelProps {
  state: CoreState;
  thought: string;
  provider: string;
  messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: string; toolCall?: { name: string; status: 'RUNNING' | 'SUCCESS' | 'ERROR' } }>;
  memoryStats: { longTerm: number | string; working: number | string; contextWindow: string };
  onDispatch: (prompt: string) => void;
}

export function ThinkingPanel({ state, messages, memoryStats, onDispatch }: ThinkingPanelProps) {
  const [inputPrompt, setInputPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || state === 'RECEIVING' || state === 'PLANNING' || state === 'EXECUTING') return;
    onDispatch(inputPrompt);
    setInputPrompt('');
  };

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden pointer-events-auto">
      
      {/* 1. TOP CONVERSATION PANEL */}
      <div className="flex-1 rounded-2xl bg-[#090514]/60 border border-[#a855f7]/25 backdrop-blur-xl p-3.5 flex flex-col justify-between overflow-hidden shadow-[0_0_20px_rgba(139,92,246,0.1)]">
        <div className="flex items-center justify-between text-xs font-mono text-[#d8b4fe] font-medium border-b border-slate-800/40 pb-2">
          <div className="flex items-center gap-2">
            <span>👤</span>
            <span className="tracking-wider uppercase">CONVERSATION</span>
          </div>
          <span className="text-[10px] text-slate-500 font-normal">REALTIME</span>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto space-y-3 my-2 pr-1 font-mono text-[11px]">
          {messages.length === 0 ? (
            <div className="text-slate-600 italic text-[10.5px] p-2">Send a prompt to trigger LEVI agent execution...</div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className="space-y-1">
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1">
                    {msg.role === 'user' ? '👤' : '⚛️'} <strong className={msg.role === 'user' ? 'text-slate-200' : 'text-[#c084fc]'}>{msg.role === 'user' ? 'You' : 'LEVI'}</strong>
                  </span>
                  <span className="text-slate-600">{msg.timestamp}</span>
                </div>
                <div className={`p-2.5 rounded-xl border ${msg.role === 'user' ? 'bg-[#120a26]/70 border-[#a855f7]/20 text-slate-200' : 'bg-[#140b2e]/90 border-[#a855f7]/30 text-slate-300'}`}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input Bar inside Conversation Panel */}
        <form onSubmit={handleSubmit} className="relative mt-1">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            disabled={state === 'RECEIVING' || state === 'PLANNING' || state === 'EXECUTING'}
            placeholder={state === 'RECEIVING' || state === 'PLANNING' || state === 'EXECUTING' ? 'Processing active command...' : 'Type a command for LEVI...'}
            className="w-full bg-[#100824]/90 border border-[#a855f7]/30 rounded-xl py-2 pl-3 pr-8 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#c084fc] disabled:opacity-50"
          />
          <button type="submit" disabled={!inputPrompt.trim() || state === 'RECEIVING' || state === 'PLANNING' || state === 'EXECUTING'} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#c084fc] hover:text-white text-xs disabled:opacity-30">
            ➔
          </button>
        </form>
      </div>

      {/* 2. BOTTOM MEMORY PANEL */}
      <div className="h-44 rounded-2xl bg-[#090514]/60 border border-[#a855f7]/25 backdrop-blur-xl p-3.5 flex flex-col justify-between shadow-[0_0_20px_rgba(139,92,246,0.1)]">
        <div className="flex items-center gap-2 text-xs font-mono text-[#d8b4fe] font-medium border-b border-slate-800/40 pb-1.5">
          <span>🧠</span>
          <span className="tracking-wider uppercase">MEMORY</span>
        </div>

        <div className="flex items-center justify-between gap-3 my-1">
          {/* Circular Memory Gauge */}
          <div className="relative w-20 h-20 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-[#1a0f35]"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-[#a855f7]"
                strokeDasharray={typeof memoryStats.working === 'number' ? `${Math.min(100, memoryStats.working * 5)}, 100` : '0, 100'}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-xs font-bold text-slate-100">{memoryStats.working === 'N/A' ? 'N/A' : `${memoryStats.working}`}</span>
              <span className="text-[7px] text-slate-400 font-mono uppercase">MEMORY USED</span>
            </div>
          </div>

          {/* Memory Metrics Breakdown */}
          <div className="flex-1 font-mono text-[10px] space-y-2">
            <div>
              <div className="text-slate-500">LONG TERM</div>
              <div className="text-slate-200 font-bold text-xs">{memoryStats.longTerm} <span className="text-[9px] font-normal text-slate-400">items</span></div>
            </div>
            <div>
              <div className="text-slate-500">WORKING</div>
              <div className="text-slate-200 font-bold text-xs">{memoryStats.working} <span className="text-[9px] font-normal text-slate-400">items</span></div>
            </div>
            <div>
              <div className="text-slate-500">CONTEXT WINDOW</div>
              <div className="text-slate-200 font-bold text-xs">{memoryStats.contextWindow}</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}


