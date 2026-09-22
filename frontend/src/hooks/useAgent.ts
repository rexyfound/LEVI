import { useState, useCallback } from 'react';
import { CoreState, StepLog, PendingAction } from '../services/types';
import { agentService } from '../services/AgentService';

export function useAgent() {
  const [coreState, setCoreState] = useState<CoreState>('IDLE');
  const [activeProvider, setActiveProvider] = useState<string>('MODEL ROUTER (GROQ/GEMINI/OPENROUTER)');
  const [currentThought, setCurrentThought] = useState<string>('Organism standing by in resting equilibrium state.');
  const [activeTool, setActiveTool] = useState<{ name: string; args: Record<string, any> } | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [history, setHistory] = useState<StepLog[]>([]);

  const dispatchCommand = useCallback(async (prompt: string) => {
    if (!prompt.trim() || coreState === 'THINKING' || coreState === 'EXECUTING') return;

    const stepId = Math.random().toString(36).substring(2, 9);
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Core transitions honestly to THINKING
    setCoreState('THINKING');
    setCurrentThought(`Evaluating intent and routing prompt: "${prompt}"`);
    setActiveTool(null);
    setPendingAction(null);

    const initialLog: StepLog = {
      id: stepId,
      timestamp,
      prompt,
      state: 'THINKING',
      provider: 'ROUTER ACTIVE',
      thought: `Evaluating prompt against available tool registries (Browser, Desktop, Memory, Files, Terminal).`
    };

    setHistory((prev) => [initialLog, ...prev]);

    const result = await agentService.runAgent(prompt);

    if (result.status === 'awaiting_confirmation' && result.pending_action) {
      setCoreState('AWAITING_APPROVAL');
      setPendingAction(result.pending_action);
      setCurrentThought('Sensitive system action requires explicit user permission.');
      setHistory((prev) =>
        prev.map((item) =>
          item.id === stepId
            ? { ...item, state: 'AWAITING_APPROVAL', response: result.response }
            : item
        )
      );
      return;
    }

    if (result.status === 'error' || result.error) {
      setCoreState('ERROR');
      setCurrentThought(`Core execution encountered an exception: ${result.error}`);
      setHistory((prev) =>
        prev.map((item) =>
          item.id === stepId
            ? { ...item, state: 'ERROR', response: result.error }
            : item
        )
      );
      setTimeout(() => setCoreState('IDLE'), 4000);
      return;
    }

    // Task completed
    setCoreState('COMPLETED');
    setCurrentThought('Task objective satisfied. Returning to resting equilibrium state.');
    setHistory((prev) =>
      prev.map((item) =>
        item.id === stepId
          ? { ...item, state: 'COMPLETED', response: result.response || 'Task executed successfully.' }
          : item
      )
    );

    setTimeout(() => {
      setCoreState('IDLE');
      setCurrentThought('Organism standing by for next cognitive trigger.');
    }, 3000);
  }, [coreState]);

  const handleApproval = useCallback(async (approved: boolean) => {
    if (!pendingAction) return;

    const actionId = pendingAction.action_id;
    
    // PART 1: Resume execution from exact paused state without re-dispatching full prompt
    setCoreState('EXECUTING');
    setCurrentThought(approved ? `Executing approved action: ${pendingAction.type}` : 'Permission denied by user. Cancelling pending tool call.');

    const res = await agentService.approveAction(actionId, approved);
    setPendingAction(null);

    if (res.success) {
      setCoreState('COMPLETED');
      setCurrentThought(approved ? `Executed: ${res.action || pendingAction.type}` : 'Action safely cancelled.');
    } else {
      setCoreState('ERROR');
      setCurrentThought(`Approval execution failed: ${res.error}`);
    }

    setTimeout(() => {
      setCoreState('IDLE');
      setCurrentThought('Organism standing by.');
    }, 2500);
  }, [pendingAction]);

  return {
    coreState,
    activeProvider,
    currentThought,
    activeTool,
    pendingAction,
    history,
    dispatchCommand,
    handleApproval
  };
}

