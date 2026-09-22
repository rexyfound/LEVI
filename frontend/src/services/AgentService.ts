import axios from 'axios';
import { AgentResponse, PendingAction } from './types';

export interface IAgentService {
  runAgent(message: string): Promise<AgentResponse>;
  approveAction(actionId: string, approved: boolean): Promise<{ success: boolean; status?: string; action?: string; error?: string }>;
}

const API_BASE_URL = 'http://localhost:8000';
const SESSION_STORAGE_KEY = 'levi.session-id';

function getSessionId(): string {
  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) return existing;
  const sessionId = window.crypto?.randomUUID?.() ?? `levi-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

class RestAgentService implements IAgentService {
  private readonly sessionId = getSessionId();

  async runAgent(message: string): Promise<AgentResponse> {
    try {
      const response = await axios.post<AgentResponse>(`${API_BASE_URL}/agent`, { message, session_id: this.sessionId }, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 60000,
      });
      return response.data;
    } catch (error: any) {
      console.error('[AgentService] Error running agent:', error);
      return {
        status: 'error',
        error: error.response?.data?.detail || error.message || 'Failed to connect to LEVI core service.'
      };
    }
  }

  async approveAction(actionId: string, approved: boolean): Promise<{ success: boolean; status?: string; error?: string }> {
    try {
      const response = await axios.post(`${API_BASE_URL}/approve`, {
        action_id: actionId,
        approved
      });
      return response.data;
    } catch (error: any) {
      console.error('[AgentService] Error approving action:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Approval request failed.'
      };
    }
  }
}

export const agentService: IAgentService = new RestAgentService();
