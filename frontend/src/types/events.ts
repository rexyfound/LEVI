export type CoreState =
  | 'IDLE'
  | 'RECEIVING'
  | 'PLANNING'
  | 'EXECUTING'
  | 'WAITING_CONFIRMATION'
  | 'VALIDATING'
  | 'COMPLETED'
  | 'FAILED'
  // Backward compatibility types:
  | 'THINKING'
  | 'AWAITING_APPROVAL'
  | 'ERROR'
  | 'MEMORY_WRITE';

export type VoiceState = 'IDLE' | 'PREPARING' | 'SPEAKING' | 'STOPPING' | 'ERROR';

export interface LeviEvent {
  type:
    | 'agent_started'
    | 'agent_state_changed'
    | 'provider_started'
    | 'provider_completed'
    | 'provider_failed'
    | 'provider_changed'
    | 'tool_started'
    | 'tool_completed'
    | 'tool_failed'
    | 'confirmation_required'
    | 'message'
    | 'log'
    | 'task_completed'
    | 'task_failed'
    | 'system_metrics'
    | 'memory_update'
    | 'repo_watcher_ready'
    | 'repo_changed'
    | 'repo_watcher_error'
    | 'swarm_started'
    | 'swarm_task_started'
    | 'swarm_task_completed'
    | 'swarm_task_failed'
    | 'swarm_completed'
    | 'voice_state_changed'
    | 'voice_error';
  timestamp: number;
  [key: string]: any;
}

export interface SystemStats {
  cpu: { usage: number };
  ram: { usage: number; used_gb: number; total_gb: number };
  gpu?: {
    name?: string;
    usage?: number;
    vram_used?: number;
    vram_total?: number;
    temperature?: number;
    status?: string;
  };
}

export interface PendingAction {
  action_id: string;
  type: string;
  data: Record<string, any>;
  requires_confirmation?: boolean;
}

export interface AgentResponse {
  status: 'complete' | 'awaiting_confirmation' | 'stopped' | 'error';
  response?: string;
  pending_action?: PendingAction;
  error?: string;
}

export interface StepLog {
  id: string;
  timestamp: string;
  prompt: string;
  state: CoreState;
  provider?: string;
  thought?: string;
  activeTool?: string;
  toolArgs?: Record<string, any>;
  response?: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  text: string;
}

export interface TimelineEntry {
  id: string;
  time: string;
  label: string;
  active?: boolean;
  check?: boolean;
  error?: boolean;
}
