import { useState, useCallback, useRef, useEffect } from "react";
import type { AgentState, Message } from "./types";
import { useAgentStore } from "./store/agentStore";
import NeuralCore from "./components/NeuralCore";
import NeuralBackground from "./components/NeuralBackground";

// ─── Types ────────────────────────────────────────────────────────────────────

type PanelId = "chat" | "system" | "memory" | "tools" | "activity" | "voice" | "vision" | null;

interface TimelineEntry {
  id: string;
  time: string;
  label: string;
  type: "info" | "success" | "error" | "system";
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

let _msgId = 0;
const nextMsgId = () => `m${++_msgId}`;
const ts = () =>
  new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

const INITIAL_MESSAGES: Message[] = [
  { id: nextMsgId(), role: "SYSTEM", content: "LEVI initialized. Adaptive Intelligence System online.", timestamp: "16:20:44" },
];

// ─── Glass surface tokens ─────────────────────────────────────────────────────

const G = {
  // Surfaces — very translucent so neural mesh shows through
  panel:      "rgba(10, 16, 28, 0.55)",
  panelDeep:  "rgba(5, 9, 18, 0.72)",
  trough:     "rgba(4, 7, 14, 0.78)",
  pill:       "rgba(14, 22, 38, 0.60)",
  // Neumorphic shadows
  raised:     "6px 6px 18px rgba(0,0,0,0.6), -3px -3px 10px rgba(255,255,255,0.035)",
  raisedLg:   "10px 10px 30px rgba(0,0,0,0.7), -5px -5px 16px rgba(255,255,255,0.04)",
  inset:      "inset 4px 4px 12px rgba(0,0,0,0.65), inset -2px -2px 8px rgba(255,255,255,0.03)",
  insetSm:    "inset 2px 2px 7px rgba(0,0,0,0.6), inset -1px -1px 4px rgba(255,255,255,0.025)",
  flatSm:     "2px 2px 6px rgba(0,0,0,0.5), -1px -1px 4px rgba(255,255,255,0.025)",
  // Borders
  border:     "1px solid rgba(255,255,255,0.07)",
  borderVi:   "1px solid rgba(139,92,246,0.25)",
  // Blur
  blur:       "blur(16px)",
  blurLg:     "blur(24px)",
};

// ─── Floating Panel ───────────────────────────────────────────────────────────

function FloatingPanel({ title, onClose, children, width = 260 }: {
  title: string; onClose: () => void; children: React.ReactNode; width?: number;
}) {
  return (
    <div
      className="absolute left-16 top-1/2 z-50 flex flex-col overflow-hidden"
      style={{
        width,
        transform: "translateY(-50%)",
        background: G.panel,
        borderRadius: 16,
        boxShadow: G.raisedLg,
        backdropFilter: G.blurLg,
        WebkitBackdropFilter: G.blurLg,
        border: G.border,
        animation: "fade-in-up 0.2s ease-out both",
      }}
    >
      <div className="flex items-center justify-between px-4 py-3" style={{ background: G.panelDeep, borderBottom: G.border }}>
        <span className="mono text-[10px] font-semibold tracking-[0.18em]" style={{ color: "var(--text-secondary)" }}>
          {title}
        </span>
        <button
          onClick={onClose}
          className="flex items-center justify-center w-5 h-5 rounded-full"
          style={{ background: G.pill, boxShadow: G.raised, border: G.border, color: "var(--text-dim)" }}
        >
          <svg width="8" height="8" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <line x1="1" y1="1" x2="9" y2="9"/><line x1="9" y1="1" x2="1" y2="9"/>
          </svg>
        </button>
      </div>
      <div className="overflow-y-auto" style={{ maxHeight: "60vh" }}>{children}</div>
    </div>
  );
}

// ─── Panel data row ───────────────────────────────────────────────────────────

function NmRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="flex items-center justify-between px-3 py-2.5 mx-3 mb-2 rounded-xl"
      style={{ background: G.trough, boxShadow: G.insetSm, border: G.border }}>
      <span className="mono text-[10px]" style={{ color: "var(--text-dim)" }}>{label}</span>
      <span className="mono text-[10px] font-medium" style={{ color: valueColor ?? "var(--text-dim)" }}>{value}</span>
    </div>
  );
}

// ─── Panel contents ───────────────────────────────────────────────────────────

function SystemPanel({ stats }: { stats?: string[][] }) {
  const rows = stats ?? [['CPU','N/A'],['RAM','N/A'],['GPU','N/A'],['NETWORK','N/A'],['UPTIME','N/A'],['LATENCY','N/A']];
  return (
    <div className="py-3">
      {rows.map(([label, value]) => <NmRow key={label} label={label} value={value} />)}
      {!stats && <p className="mono text-[9px] text-center mt-1 mb-3" style={{ color: "var(--text-dim)" }}>Waiting for local telemetry</p>}
    </div>
  );
}

function MemoryPanel({ stats }: { stats: { longTerm: number | string; working: number | string; contextWindow: string } }) {
  return (
    <div className="py-3">
      <NmRow label="LONG-TERM" value={String(stats.longTerm)} />
      <NmRow label="RECENT" value={String(stats.working)} />
      <NmRow label="SEARCH" value="READY" valueColor="var(--success)" />
      <div className="mx-3 mb-2 mt-1 px-3 py-2.5 rounded-xl flex items-center"
        style={{ background: G.trough, boxShadow: G.insetSm, border: G.border }}>
        <span className="mono text-[10px]" style={{ color: "var(--text-dim)" }}>Search memory...</span>
      </div>
      <p className="mono text-[10px] px-4 pb-2" style={{ color: "var(--text-dim)" }}>Context: {stats.contextWindow}</p>
    </div>
  );
}

function ToolsPanel({ tools }: { tools: Record<string, { name: string; status: string }> }) {
  const rows = Object.values(tools);
  return (
    <div className="py-3">
      {rows.map(({ name, status }) => (
        <div key={name} className="flex items-center justify-between mx-3 mb-2 px-3 py-2.5 rounded-xl" style={{ background: G.trough, boxShadow: G.insetSm, border: G.border }}>
          <span className="mono text-[10px] font-medium" style={{ color: "var(--text-secondary)" }}>{name}</span>
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: status === "ERROR" ? "var(--error)" : status === "ACTIVE" ? "var(--violet)" : "var(--success)" }} />
            <span className="mono text-[9px]" style={{ color: status === "ERROR" ? "var(--error)" : "var(--success)" }}>{status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function ActivityPanel({ entries }: { entries: TimelineEntry[] }) {
  const colors = { info:"var(--text-dim)", success:"var(--success)", error:"var(--error)", system:"var(--cyan)" };
  return (
    <div className="py-3 px-4">
      {entries.length === 0 && <p className="mono text-[10px] text-center py-4" style={{ color: "var(--text-dim)" }}>No activity yet</p>}
      {entries.map((e, i) => (
        <div key={e.id} className="flex gap-2.5 py-1">
          <div className="flex flex-col items-center" style={{ width: 12 }}>
            <div className="w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0" style={{ background: colors[e.type] }} />
            {i < entries.length - 1 && <div className="flex-1 w-px mt-0.5" style={{ background: "rgba(255,255,255,0.05)", minHeight: 10 }} />}
          </div>
          <div className="pb-1">
            <div className="mono text-[9px]" style={{ color: "var(--text-dim)" }}>{e.time}</div>
            <div className="text-[11px]" style={{ color: colors[e.type] }}>{e.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function VoicePanel({ active }: { active: boolean }) {
  return (
    <div className="py-3">
      {[['STATUS', active ? 'LISTENING' : 'IDLE'],['VOICE','LEVI'],['SPEED','0.95×'],['STYLE','Calm']].map(([label, value]) => (
        <NmRow key={label} label={label} value={value} valueColor={active && label === 'STATUS' ? 'var(--violet-light)' : undefined} />
      ))}
    </div>
  );
}

function VisionPanel() {
  return (
    <div className="py-3">
      <NmRow label="SCREEN CAPTURE" value="READY" valueColor="var(--success)" />
      <div className="mx-3 flex items-center justify-center rounded-xl mb-2"
        style={{ height: 72, background: G.trough, boxShadow: G.insetSm, border: G.border }}>
        <span className="mono text-[10px]" style={{ color: "var(--text-dim)" }}>No capture active</span>
      </div>
      <p className="mono text-[10px] px-4 pb-2" style={{ color: "var(--text-dim)" }}>DETECTED — none</p>
    </div>
  );
}

// ─── Chat message ─────────────────────────────────────────────────────────────

function ChatMessage({ msg }: { msg: Message }) {
  if (msg.role === "SYSTEM") {
    return (
      <div className="flex justify-center py-1">
        <span className="mono text-[10px] px-3 py-1 rounded-full"
          style={{ color: "var(--text-dim)", background: G.trough, boxShadow: G.insetSm, border: G.border }}>
          {msg.content}
        </span>
      </div>
    );
  }

  const isUser = msg.role === "USER";
  return (
    <div className={`flex flex-col gap-1 animate-fade-up ${isUser ? "items-end" : "items-start"}`}>
      <span className="mono text-[9px] px-1" style={{ color: "var(--text-dim)" }}>
        {isUser ? "YOU" : "LEVI"} · {msg.timestamp}
      </span>
      <div
        className="px-4 py-3 max-w-sm text-[12px] leading-relaxed"
        style={{
          borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
          background: isUser ? "rgba(30,20,55,0.55)" : G.panel,
          backdropFilter: G.blur,
          WebkitBackdropFilter: G.blur,
          border: isUser ? G.borderVi : G.border,
          boxShadow: G.raised,
          color: "var(--text-primary)",
          fontFamily: "var(--font-body)",
        }}
      >
        {msg.content}
      </div>
      {msg.toolName && msg.toolStatus && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl mono text-[10px]"
          style={{ background: G.trough, boxShadow: G.insetSm, border: G.border,
            color: msg.toolStatus === "SUCCESS" ? "var(--success)" : msg.toolStatus === "ERROR" ? "var(--error)" : "var(--warning)" }}>
          <span style={{ color: "var(--text-dim)" }}>fn/</span>
          {msg.toolName} · {msg.toolStatus}
        </div>
      )}
    </div>
  );
}

// ─── Left rail buttons ────────────────────────────────────────────────────────

const RAIL: Array<{ id: PanelId; label: string; d: string }> = [
  { id: "chat",     label: "Chat",     d: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" },
  { id: "system",   label: "System",   d: "M2 3h20v14H2zM8 21h8M12 17v4" },
  { id: "memory",   label: "Memory",   d: "M12 2C7 2 3 3.34 3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5c0-1.66-4-3-9-3zM3 12c0 1.66 4 3 9 3s9-1.34 9-3" },
  { id: "tools",    label: "Tools",    d: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" },
  { id: "activity", label: "Activity", d: "M22 12h-4l-3 9L9 3l-3 9H2" },
  { id: "voice",    label: "Voice",    d: "M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3zM19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" },
  { id: "vision",   label: "Vision",   d: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 100 6 3 3 0 000-6z" },
];

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const {
    coreState,
    messages: backendMessages,
    timeline: backendTimeline,
    tools,
    systemStats,
    memoryStats,
    isWsConnected,
    pendingAction,
    dispatchCommand,
    handleApproval,
  } = useAgentStore();
  const [input, setInput] = useState("");
  const [openPanel, setOpenPanel] = useState<PanelId>(null);
  const [voiceActive, setVoiceActive] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  const agentState = (coreState === "WAITING_CONFIRMATION" || coreState === "AWAITING_APPROVAL")
    ? "WAITING_FOR_APPROVAL"
    : (coreState === "ERROR" ? "FAILED" : coreState) as AgentState;
  const messages: Message[] = backendMessages.map((message) => ({
    id: message.id,
    role: message.role === "user" ? "USER" : "LEVI",
    content: message.content,
    timestamp: message.timestamp,
    toolName: message.toolCall?.name,
    toolStatus: message.toolCall?.status,
  }));
  const timeline: TimelineEntry[] = backendTimeline.map((entry) => ({
    id: entry.id,
    time: entry.time,
    label: entry.label,
    type: entry.error ? "error" : entry.check ? "success" : entry.active ? "info" : "system",
  }));
  const hasChatMessages = messages.length > 0;
  const isProcessing = ["RECEIVING", "PLANNING", "EXECUTING", "VALIDATING", "WAITING_FOR_APPROVAL", "SPEAKING"].includes(agentState);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isProcessing) return;
    setInput("");
    await dispatchCommand(text);
  }, [dispatchCommand, input, isProcessing]);

  const stateLabel: Record<AgentState, string> = {
    IDLE: "Listening...", RECEIVING: "Receiving...", PLANNING: "Planning...",
    EXECUTING: "Executing...", WAITING_FOR_APPROVAL: "Awaiting approval...",
    VALIDATING: "Validating...", COMPLETED: "Completed.", FAILED: "Failed.", SPEAKING: "Speaking...",
  };

  const systemValues = systemStats ? [
    ["CPU", `${Math.round(systemStats.cpu.usage)}%`],
    ["RAM", `${Math.round(systemStats.ram.usage)}%`],
    ["GPU", systemStats.gpu?.status === "unavailable" ? "N/A" : `${Math.round(systemStats.gpu?.usage ?? 0)}%`],
    ["NETWORK", isWsConnected ? "CONNECTED" : "OFFLINE"],
    ["UPTIME", "LOCAL"],
    ["LATENCY", isWsConnected ? "LIVE" : "N/A"],
  ] : undefined;

  return (
    <div className="w-full h-full flex overflow-hidden relative" style={{ background: "#04080F", fontFamily: "var(--font-ui)" }}>
      <NeuralBackground />

      <div className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-5" style={{ height: 50, pointerEvents: "none" }}>
        <div style={{ pointerEvents: "auto" }}>
          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-full" style={{ background: G.pill, boxShadow: G.raised, backdropFilter: G.blur, WebkitBackdropFilter: G.blur, border: G.border }}>
            <div className="w-2 h-2 rounded-full animate-pulse-core" style={{ background: "var(--violet)", boxShadow: "0 0 6px var(--violet)" }} />
            <span className="text-[12px] font-bold tracking-[0.28em]" style={{ color: "var(--text-primary)" }}>LEVI</span>
            <span className="mono text-[9px] tracking-[0.1em] ml-1" style={{ color: "var(--text-dim)" }}>AIS</span>
          </div>
        </div>
        <div style={{ pointerEvents: "auto" }}>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: G.pill, boxShadow: G.raised, backdropFilter: G.blur, WebkitBackdropFilter: G.blur, border: G.border }}>
            <span className="inline-block w-1.5 h-1.5 rounded-full animate-status" style={{ background: isWsConnected ? "var(--success)" : "var(--warning)", boxShadow: "0 0 4px currentColor" }} />
            <span className="mono text-[9px] tracking-[0.12em]" style={{ color: isWsConnected ? "var(--success)" : "var(--warning)" }}>{isWsConnected ? "OPTIMAL" : "LOCAL OFFLINE"}</span>
          </div>
        </div>
      </div>

      <div className="absolute left-3 top-1/2 z-40 flex flex-col items-center gap-1.5 py-3 rounded-2xl" style={{ transform: "translateY(-50%)", background: G.panel, boxShadow: G.raisedLg, backdropFilter: G.blurLg, WebkitBackdropFilter: G.blurLg, border: G.border }}>
        {RAIL.map(({ id, label, d }) => {
          const active = openPanel === id;
          return (
            <button key={id} onClick={() => setOpenPanel((p) => p === id ? null : id)} title={label} className="flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-200" style={{ color: active ? "var(--violet-light)" : "var(--text-dim)", background: active ? G.trough : "transparent", boxShadow: active ? G.insetSm : G.flatSm }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
            </button>
          );
        })}
      </div>

      {openPanel && (
        <div className="absolute inset-0 z-30" style={{ pointerEvents: "none" }}>
          <div style={{ position: "absolute", left: 48, top: 0, bottom: 0, pointerEvents: "auto" }}>
            {openPanel === "system" && <FloatingPanel title="SYSTEM" onClose={() => setOpenPanel(null)}><SystemPanel stats={systemValues} /></FloatingPanel>}
            {openPanel === "memory" && <FloatingPanel title="MEMORY" onClose={() => setOpenPanel(null)}><MemoryPanel stats={memoryStats} /></FloatingPanel>}
            {openPanel === "tools" && <FloatingPanel title="TOOLS" onClose={() => setOpenPanel(null)}><ToolsPanel tools={tools} /></FloatingPanel>}
            {openPanel === "activity" && <FloatingPanel title="ACTIVITY" onClose={() => setOpenPanel(null)} width={230}><ActivityPanel entries={timeline} /></FloatingPanel>}
            {openPanel === "voice" && <FloatingPanel title="VOICE" onClose={() => setOpenPanel(null)}><VoicePanel active={voiceActive} /></FloatingPanel>}
            {openPanel === "vision" && <FloatingPanel title="VISION" onClose={() => setOpenPanel(null)}><VisionPanel /></FloatingPanel>}
            {openPanel === "chat" && <FloatingPanel title="CONVERSATION" onClose={() => setOpenPanel(null)} width={320}><div className="p-4 flex flex-col gap-3">{messages.map((m) => <ChatMessage key={m.id} msg={m} />)}</div></FloatingPanel>}
          </div>
        </div>
      )}

      {pendingAction && (
        <div className="absolute inset-0 z-[60] flex items-center justify-center" style={{ background: "rgba(2, 4, 10, 0.52)", backdropFilter: "blur(7px)" }}>
          <div className="w-[min(420px,calc(100vw-32px))] rounded-2xl p-5" style={{ background: G.panelDeep, border: G.borderVi, boxShadow: G.raisedLg }}>
            <div className="mono text-[10px] tracking-[0.18em] mb-3" style={{ color: "var(--warning)" }}>CONFIRMATION REQUIRED</div>
            <div className="text-[13px] leading-relaxed mb-5" style={{ color: "var(--text-primary)" }}>{pendingAction.type}</div>
            <div className="flex justify-end gap-2">
              <button className="px-4 py-2 rounded-xl mono text-[10px]" style={{ color: "var(--text-dim)", background: G.trough, border: G.border }} onClick={() => handleApproval(false)}>DENY</button>
              <button className="px-4 py-2 rounded-xl mono text-[10px]" style={{ color: "var(--violet-light)", background: "rgba(30,18,55,0.7)", border: G.borderVi }} onClick={() => handleApproval(true)}>APPROVE</button>
            </div>
          </div>
        </div>
      )}

      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center" style={{ paddingTop: 50 }}>
        {!hasChatMessages && (
          <div className="flex flex-col items-center gap-8" style={{ width: "100%", maxWidth: 560 }}>
            <div className="rounded-full flex items-center justify-center" style={{ width: 320, height: 320, background: G.panel, boxShadow: G.raisedLg, backdropFilter: G.blur, border: G.borderVi }}>
              <div className="rounded-full flex items-center justify-center" style={{ width: 278, height: 278, background: "rgba(4,7,14,0.6)", boxShadow: G.inset }}>
                <div style={{ width: 248, height: 248 }}><NeuralCore state={agentState} /></div>
              </div>
            </div>
            <p className="text-[13px] font-light tracking-[0.1em] transition-all duration-500" style={{ color: "var(--text-secondary)", fontFamily: "var(--font-body)", marginTop: -16 }}>{stateLabel[agentState]}</p>
            <CommandBar input={input} setInput={setInput} onSend={handleSend} voiceActive={voiceActive} setVoiceActive={setVoiceActive} isProcessing={isProcessing} />
          </div>
        )}

        {hasChatMessages && (
          <div className="flex flex-col w-full h-full" style={{ maxWidth: 640, paddingBottom: 24 }}>
            <div className="flex-shrink-0 flex items-center justify-center pt-4 pb-2"><div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: G.panel, boxShadow: G.raised, backdropFilter: G.blur, border: G.border }}><span className="inline-block w-1.5 h-1.5 rounded-full animate-status" style={{ background: "var(--violet)", boxShadow: "0 0 4px var(--violet)" }} /><span className="mono text-[10px] tracking-[0.14em]" style={{ color: "var(--text-secondary)" }}>{stateLabel[agentState]}</span></div></div>
            <div ref={chatScrollRef} className="flex-1 overflow-y-auto px-4 py-2"><div className="flex flex-col gap-3">{messages.map((m) => <ChatMessage key={m.id} msg={m} />)}{isProcessing && <div className="flex items-center gap-2 pl-1"><span className="mono text-[10px]" style={{ color: "var(--text-dim)" }}>LEVI</span>{[0,1,2].map((i) => <span key={i} className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: "var(--violet-light)", animation: "particle-blink 1.2s ease-in-out infinite", animationDelay: `${i*0.2}s` }} />)}</div>}</div></div>
            <div className="flex-shrink-0 pt-3 px-4"><CommandBar input={input} setInput={setInput} onSend={handleSend} voiceActive={voiceActive} setVoiceActive={setVoiceActive} isProcessing={isProcessing} /></div>
          </div>
        )}
      </div>

      <button className="absolute bottom-4 right-4 z-40 flex items-center justify-center w-8 h-8 rounded-full" title="Local LEVI controls" style={{ background: G.pill, boxShadow: G.raised, border: G.border, color: "var(--text-secondary)" }} onClick={() => setOpenPanel((p) => p === "system" ? null : "system")}>?</button>
    </div>
  );
}

// ─── Command bar ──────────────────────────────────────────────────────────────

function CommandBar({ input, setInput, onSend, voiceActive, setVoiceActive, isProcessing }: {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
  voiceActive: boolean;
  setVoiceActive: (v: boolean | ((p: boolean) => boolean)) => void;
  isProcessing: boolean;
}) {
  return (
    <div className="flex flex-col items-stretch gap-2" style={{ width: "100%" }}>
      {/* Input trough */}
      <div className="flex items-center gap-3 px-4 py-3 rounded-2xl"
        style={{ background: G.trough, boxShadow: G.inset, border: G.border, backdropFilter: G.blurLg, WebkitBackdropFilter: G.blurLg }}>

        <span className="mono text-[15px] font-light flex-shrink-0" style={{ color: "var(--violet)" }}>›</span>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSend()}
          placeholder="Ask LEVI anything..."
          disabled={isProcessing}
          autoFocus
          className="flex-1 bg-transparent outline-none text-[13px]"
          style={{ color: "var(--text-primary)", fontFamily: "var(--font-body)" }}
        />

        {/* Mic */}
        <button
          onClick={() => setVoiceActive((v) => !v)}
          className="flex items-center justify-center w-8 h-8 rounded-xl transition-all duration-200 flex-shrink-0"
          style={{
            background: G.pill,
            boxShadow: voiceActive ? G.insetSm : G.raised,
            color: voiceActive ? "var(--violet-light)" : "var(--text-dim)",
            border: G.border,
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
            <path d="M19 10v2a7 7 0 01-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </button>

        {/* Send */}
        <button
          onClick={onSend}
          disabled={!input.trim() || isProcessing}
          className="flex items-center justify-center w-8 h-8 rounded-xl transition-all duration-200 disabled:opacity-25 flex-shrink-0"
          style={{
            background: "rgba(30,18,55,0.7)",
            boxShadow: `${G.raised}, inset 0 0 0 1px rgba(139,92,246,0.35)`,
            color: "var(--violet-light)",
          }}
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>

      {/* Voice wave */}
      {voiceActive && (
        <div className="flex items-center justify-center gap-2">
          <span className="animate-status inline-block w-1.5 h-1.5 rounded-full" style={{ background: "var(--error)" }} />
          <span className="mono text-[10px]" style={{ color: "var(--error)" }}>LISTENING</span>
          <div className="flex items-end gap-0.5 h-3">
            {[1,2,4,3,5,3,2].map((h, i) => (
              <div key={i} className="w-0.5 rounded-full animate-voice"
                style={{ background: "var(--error)", height: `${h*2}px`, animationDelay: `${i*0.1}s` }} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
