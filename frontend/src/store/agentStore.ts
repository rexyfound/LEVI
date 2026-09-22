import { useState, useEffect, useCallback } from 'react';
import { CoreState, LeviEvent, SystemStats, PendingAction, LogEntry, TimelineEntry, VoiceState } from '../types/events';
import { leviSocket } from '../services/leviSocket';
import { agentService } from '../services/AgentService';

export interface ToolStatus {
  name: string;
  desc: string;
  icon: string;
  status: 'IDLE' | 'ACTIVE' | 'SUCCESS' | 'ERROR';
}

export function useAgentStore() {
  const [coreState, setCoreState] = useState<CoreState>('IDLE');
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [activeProvider, setActiveProvider] = useState<string>('N/A');
  const [activeModel, setActiveModel] = useState<string>('N/A');
  const [currentThought, setCurrentThought] = useState<string>('System idle.');
  const [activeTool, setActiveTool] = useState<{ name: string; args: Record<string, any> } | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  
  // Real Data Streams
  const [messages, setMessages] = useState<Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: string; toolCall?: { name: string; status: 'RUNNING' | 'SUCCESS' | 'ERROR' } }>>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [memoryStats, setMemoryStats] = useState<{ longTerm: number | string; working: number | string; contextWindow: string }>({
    longTerm: 'N/A',
    working: 'N/A',
    contextWindow: 'N/A'
  });

  // Registered Tool Statuses Map
  const [tools, setTools] = useState<Record<string, ToolStatus>>({
    browser_open: { name: 'BROWSER', desc: 'Web search & browsing', icon: '🌐', status: 'IDLE' },
    launch_app: { name: 'DESKTOP', desc: 'Desktop automation', icon: '💻', status: 'IDLE' },
    vision_analyze: { name: 'VISION', desc: 'Screen & image analysis', icon: '👁️', status: 'IDLE' },
    run_terminal: { name: 'TERMINAL', desc: 'Command line execution', icon: '⌨️', status: 'IDLE' },
    memory_search: { name: 'MEMORY', desc: 'Knowledge & context', icon: '💾', status: 'IDLE' },
    list_files: { name: 'PLANNER', desc: 'Task planning & reasoning', icon: '🕸️', status: 'IDLE' },
  });

  // Subscribe to WebSocket Connection & Events
  useEffect(() => {
    leviSocket.connect();

    const unsubConn = leviSocket.onConnectionChange((connected) => {
      setIsWsConnected(connected);
    });

    const unsubEvent = leviSocket.onEvent((event: LeviEvent) => {
      const timeStr = new Date(event.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      // Add to live log console
      const logText = `[${timeStr}] ${event.type.toUpperCase()}${event.tool ? `: ${event.tool}` : event.provider ? `: ${event.provider}` : event.state ? `: ${event.state}` : ''}`;
      setLogs((prev) => [...prev.slice(-99), { id: Math.random().toString(), timestamp: timeStr, text: logText }]);

      switch (event.type) {
        case 'agent_started':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: 'User Command Received', active: true }]);
          break;

        case 'swarm_started':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Swarm started (${event.task_count ?? 0} workers)`, active: true }]);
          break;

        case 'swarm_task_started':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `${event.role || 'Worker'} started`, active: true }]);
          break;

        case 'swarm_task_completed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `${event.role || 'Worker'} completed`, active: true, check: true }]);
          break;

        case 'swarm_task_failed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `${event.role || 'Worker'} failed`, active: false, error: true }]);
          break;

        case 'swarm_completed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Swarm ${event.status || 'completed'}`, active: event.status !== 'partial', check: event.status !== 'partial', error: event.status === 'partial' }]);
          break;

        case 'agent_state_changed':
          setCoreState(event.state as CoreState);
          if (event.state === 'IDLE') {
            setActiveTool(null);
            setPendingAction(null);
          }
          break;

        case 'voice_state_changed': {
          const state = event.state as VoiceState;
          setVoiceState(state);
          if (state === 'PREPARING' || state === 'SPEAKING') {
            setTimeline((prev) => [...prev, {
              id: Math.random().toString(),
              time: timeStr,
              label: state === 'PREPARING' ? 'Voice preparing' : 'Voice speaking',
              active: true,
            }]);
          }
          break;
        }

        case 'voice_error':
          setVoiceState('ERROR');
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: 'Voice unavailable', active: false, error: true }]);
          break;

        case 'provider_started':
        case 'provider_changed':
          setActiveProvider(event.provider || 'N/A');
          setActiveModel(event.model || 'N/A');
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Provider: ${event.provider}`, active: true }]);
          break;

        case 'tool_started':
          setActiveTool({ name: event.tool, args: event.arguments || {} });
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Tool Started: ${event.tool}`, active: true }]);
          // Update tool status badge
          setTools((prev) => {
            const updated = { ...prev };
            Object.keys(updated).forEach((k) => {
              if (k === event.tool || updated[k].name.toLowerCase() === event.tool.toLowerCase()) {
                updated[k].status = 'ACTIVE';
              }
            });
            return updated;
          });
          break;

        case 'tool_completed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Tool Completed: ${event.tool}`, active: true, check: true }]);
          setTools((prev) => {
            const updated = { ...prev };
            Object.keys(updated).forEach((k) => {
              if (k === event.tool || updated[k].name.toLowerCase() === event.tool.toLowerCase()) {
                updated[k].status = 'SUCCESS';
              }
            });
            return updated;
          });
          break;

        case 'tool_failed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Tool Failed: ${event.tool}`, active: false, error: true }]);
          setTools((prev) => {
            const updated = { ...prev };
            Object.keys(updated).forEach((k) => {
              if (k === event.tool || updated[k].name.toLowerCase() === event.tool.toLowerCase()) {
                updated[k].status = 'ERROR';
              }
            });
            return updated;
          });
          break;

        case 'confirmation_required':
          setPendingAction(event.pending_action);
          setCoreState('WAITING_CONFIRMATION');
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: 'Confirmation Required', active: true }]);
          break;

        case 'message':
          if (event.role === 'assistant') {
            setMessages((prev) => [
              ...prev,
              { id: Math.random().toString(), role: 'assistant', content: event.content, timestamp: timeStr }
            ]);
          }
          break;

        case 'task_completed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: 'Task Completed', active: true, check: true }]);
          break;

        case 'task_failed':
          setTimeline((prev) => [...prev, { id: Math.random().toString(), time: timeStr, label: `Task Failed: ${event.error || ''}`, active: false, error: true }]);
          break;

        case 'system_metrics':
          setSystemStats({
            cpu: event.cpu || { usage: 0 },
            ram: event.ram || { usage: 0, used_gb: 0, total_gb: 0 },
            gpu: event.gpu
          });
          break;

        case 'memory_update':
          setMemoryStats({
            longTerm: event.long_term_count ?? 'N/A',
            working: event.working_count ?? 'N/A',
            contextWindow: event.context_window ?? 'N/A'
          });
          break;

        case 'repo_watcher_ready':
          setTimeline((prev) => [
            ...prev,
            { id: Math.random().toString(), time: timeStr, label: `Repository watcher ready (${event.file_count ?? 0} files)`, active: true, check: true }
          ]);
          break;

        case 'repo_changed': {
          const count = event.change_count ?? event.changes?.length ?? 0;
          const firstPath = event.changes?.[0]?.path;
          setTimeline((prev) => [
            ...prev,
            { id: Math.random().toString(), time: timeStr, label: `Repository changed: ${count} file${count === 1 ? '' : 's'}${firstPath ? ` (${firstPath})` : ''}`, active: true }
          ]);
          setLogs((prev) => [
            ...prev.slice(-99),
            {
              id: Math.random().toString(),
              timestamp: timeStr,
              text: `REPO_CHANGED: ${count} file${count === 1 ? '' : 's'} detected${event.truncated ? ' (first 200 shown)' : ''}`
            }
          ]);
          break;
        }

        case 'repo_watcher_error':
          setTimeline((prev) => [
            ...prev,
            { id: Math.random().toString(), time: timeStr, label: `Repository watcher error: ${event.error || 'unknown error'}`, active: false, error: true }
          ]);
          break;
      }
    });

    return () => {
      unsubConn();
      unsubEvent();
    };
  }, []);

  const dispatchCommand = useCallback(async (prompt: string) => {
    if (!prompt.trim() || coreState === 'RECEIVING' || coreState === 'PLANNING' || coreState === 'EXECUTING') return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Instantly show USER message
    setMessages((prev) => [...prev, { id: Math.random().toString(), role: 'user', content: prompt, timestamp: timeStr }]);
    
    // Call backend API
    await agentService.runAgent(prompt);
  }, [coreState]);

  const handleApproval = useCallback(async (approved: boolean) => {
    if (!pendingAction) return;

    const actionId = pendingAction.action_id;
    setPendingAction(null);

    await agentService.approveAction(actionId, approved);
  }, [pendingAction]);

  return {
    coreState,
    voiceState,
    activeProvider,
    activeModel,
    currentThought,
    activeTool,
    pendingAction,
    messages,
    logs,
    timeline,
    systemStats,
    isWsConnected,
    memoryStats,
    tools,
    dispatchCommand,
    handleApproval
  };
}
