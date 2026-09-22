export type AgentState =
  | "IDLE"
  | "RECEIVING"
  | "PLANNING"
  | "EXECUTING"
  | "WAITING_FOR_APPROVAL"
  | "VALIDATING"
  | "COMPLETED"
  | "FAILED"
  | "PREPARING"
  | "SPEAKING";

export type ToolStatus = "IDLE" | "ACTIVE" | "SUCCESS" | "ERROR" | "WAITING" | "READY" | "SPEAKING" | "ANALYZING";

export type ModelStatus = "CONNECTED" | "SWITCHING" | "FAILED" | "OFFLINE";

export interface Message {
  id: string;
  role: "USER" | "LEVI" | "TOOL" | "SYSTEM";
  content: string;
  timestamp: string;
  toolName?: string;
  toolStatus?: "SUCCESS" | "ERROR" | "RUNNING";
  subMessages?: Message[];
}

export interface ConsoleLine {
  id: string;
  timestamp: string;
  text: string;
  type: "info" | "success" | "error" | "warn" | "system";
}

export interface PipelineStage {
  id: string;
  label: string;
  status: "inactive" | "active" | "completed" | "failed" | "waiting";
}
