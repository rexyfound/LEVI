import { useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, ArrowRight, ShieldCheck, Lock } from 'lucide-react';
import { PendingAction } from '../../types/events';



interface ApprovalOverlayProps {
  action: PendingAction;
  onConfirm: (approved: boolean) => void;
  originalPrompt?: string;
}

export function ApprovalOverlay({ action, onConfirm, originalPrompt }: ApprovalOverlayProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        onConfirm(true);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onConfirm(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onConfirm]);

  const getToolDisplayName = (type: string) => {
    switch (type) {
      case 'run_terminal': return 'Terminal Command Execution';
      case 'overwrite_file': return 'Workspace File Overwrite';
      case 'launch_app': return 'Launch Desktop Application';
      default: return type.replace('_', ' ').toUpperCase();
    }
  };

  const getRequestedPermissions = (type: string, data: Record<string, any>) => {
    if (type === 'run_terminal') {
      return [
        `Execute Shell Command: "${data.command || ''}"`,
        'Access Terminal Output & Environment'
      ];
    }
    if (type === 'overwrite_file') {
      return [
        `Modify File: "${data.path || ''}"`,
        'Overwrite Existing Content on Disk'
      ];
    }
    if (type === 'launch_app') {
      return [
        `Launch Process: "${data.path || ''}"`,
        'Create New Application Subprocess'
      ];
    }
    return [JSON.stringify(data)];
  };

  const getDeniedCapabilities = () => [
    'System Registry Modification',
    'Root / Admin Escalation',
    'Unrestricted File System Access Outside Workspace'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-200">
      
      {/* Outer Glow & Cinematic Frame */}
      <div className="relative w-full max-w-lg bg-[#07090e]/95 border border-amber-500/40 rounded-2xl p-6 shadow-[0_0_50px_rgba(245,158,11,0.15)] space-y-6 text-mono overflow-hidden">
        
        {/* Animated Warning Pulse Line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500/0 via-amber-500 to-amber-500/0 animate-pulse" />

        {/* Header */}
        <div className="flex items-center gap-3.5 border-b border-amber-500/20 pb-4">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono tracking-widest text-amber-500/80 uppercase">Security Checkpoint</span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
            </div>
            <h3 className="text-base font-bold text-slate-100 uppercase tracking-wider">LEVI PERMISSION REQUEST</h3>
          </div>
        </div>

        {/* Reason Context */}
        <div className="space-y-1.5">
          <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
            <span>Tool Target:</span>
            <span className="text-amber-400 font-semibold">{getToolDisplayName(action.type)}</span>
          </div>
          {originalPrompt && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-300 italic">
              "{originalPrompt}"
            </div>
          )}
        </div>

        {/* Requested Permissions vs Denied Capabilities */}
        <div className="grid grid-cols-1 gap-3">
          {/* Requested */}
          <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-400 uppercase tracking-wide">
              <ShieldCheck className="w-3.5 h-3.5" />
              Requested Permissions
            </div>
            <ul className="space-y-1 text-xs text-slate-300">
              {getRequestedPermissions(action.type, action.data).map((perm, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="font-mono text-[11.5px]">{perm}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Denied Capabilities */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wide">
              <Lock className="w-3.5 h-3.5 text-slate-500" />
              Guaranteed Denied Capabilities
            </div>
            <ul className="space-y-1 text-xs text-slate-400">
              {getDeniedCapabilities().map((cap, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <XCircle className="w-3.5 h-3.5 text-slate-600 shrink-0 mt-0.5" />
                  <span className="font-mono text-[11px]">{cap}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Action Controls */}
        <div className="pt-2 space-y-2">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onConfirm(false)}
              className="flex-1 flex items-center justify-center gap-2 bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-red-500/50 text-slate-300 font-semibold py-3 rounded-xl text-xs transition-all duration-200"
            >
              <XCircle className="w-4 h-4 text-red-400" />
              DENY [ESC]
            </button>
            <button
              onClick={() => onConfirm(true)}
              className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold py-3 rounded-xl text-xs transition-all duration-200 shadow-[0_0_20px_rgba(245,158,11,0.4)]"
            >
              <CheckCircle2 className="w-4 h-4" />
              APPROVE [ENTER]
              <ArrowRight className="w-3.5 h-3.5 opacity-80" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

