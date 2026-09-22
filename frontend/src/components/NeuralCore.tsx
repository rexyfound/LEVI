import { useRef, useEffect } from "react";
import type { AgentState } from "../types";

// Per-state visual config
const STATE_CFG: Record<AgentState, {
  rgb: [number, number, number];
  rgb2: [number, number, number];
  intensity: number;   // 0-1 overall brightness multiplier
  spikeLen: number;    // spike arm length as fraction of radius
  spikeCount: number;  // number of primary spikes (doubled with secondaries)
  orbitSpeed: number;  // particle orbit speed (radians/frame)
  rotSpeed: number;    // spike rotation speed (radians/frame)
  particleRings: number;
  label: string;
  labelRgb: [number, number, number];
}> = {
  IDLE:                 { rgb:[139,92,246],  rgb2:[100,60,220],  intensity:0.60, spikeLen:1.20, spikeCount:4, orbitSpeed:0.004, rotSpeed:0.003,  particleRings:2, label:"IDLE",                 labelRgb:[167,139,250] },
  RECEIVING:            { rgb:[167,139,250], rgb2:[139,92,246],  intensity:0.72, spikeLen:1.35, spikeCount:4, orbitSpeed:0.007, rotSpeed:0.006,  particleRings:2, label:"RECEIVING",            labelRgb:[76,201,240]  },
  PLANNING:             { rgb:[76,201,240],  rgb2:[50,160,200],  intensity:0.78, spikeLen:1.50, spikeCount:6, orbitSpeed:0.010, rotSpeed:0.010,  particleRings:3, label:"PLANNING",             labelRgb:[76,201,240]  },
  EXECUTING:            { rgb:[139,92,246],  rgb2:[180,100,255], intensity:0.95, spikeLen:1.80, spikeCount:6, orbitSpeed:0.016, rotSpeed:0.018,  particleRings:3, label:"EXECUTING",            labelRgb:[167,139,250] },
  WAITING_FOR_APPROVAL: { rgb:[251,191,36],  rgb2:[220,150,20],  intensity:0.65, spikeLen:1.10, spikeCount:4, orbitSpeed:0.004, rotSpeed:0.002,  particleRings:2, label:"AWAITING APPROVAL",    labelRgb:[251,191,36]  },
  VALIDATING:           { rgb:[76,201,240],  rgb2:[100,220,250], intensity:0.82, spikeLen:1.55, spikeCount:6, orbitSpeed:0.012, rotSpeed:0.013,  particleRings:3, label:"VALIDATING",           labelRgb:[76,201,240]  },
  COMPLETED:            { rgb:[52,211,153],  rgb2:[30,180,120],  intensity:0.88, spikeLen:1.60, spikeCount:4, orbitSpeed:0.008, rotSpeed:0.007,  particleRings:2, label:"COMPLETED",            labelRgb:[52,211,153]  },
  FAILED:               { rgb:[248,113,113], rgb2:[200,70,70],   intensity:0.68, spikeLen:1.10, spikeCount:4, orbitSpeed:0.005, rotSpeed:0.004,  particleRings:2, label:"FAILED",              labelRgb:[248,113,113] },
  PREPARING:            { rgb:[192,132,252], rgb2:[139,92,246],  intensity:0.70, spikeLen:1.30, spikeCount:5, orbitSpeed:0.007, rotSpeed:0.007,  particleRings:2, label:"VOICE PREPARING",    labelRgb:[216,180,254] },
  SPEAKING:             { rgb:[167,139,250], rgb2:[139,92,246],  intensity:0.78, spikeLen:1.45, spikeCount:6, orbitSpeed:0.009, rotSpeed:0.009,  particleRings:3, label:"SPEAKING",            labelRgb:[167,139,250] },
};

interface OrbitParticle {
  angle: number;
  ring: number;        // which orbit ring (0,1,2)
  speed: number;
  size: number;
  opacity: number;
  phase: number;
  phaseSpeed: number;
}

export default function NeuralCore({ state }: { state: AgentState }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef  = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    const SIZE = canvas.width; // square canvas
    const CX   = SIZE / 2;
    const CY   = SIZE / 2;
    const BASE_R = SIZE * 0.28; // base orbit radius

    // Generate orbit particles
    const PARTICLES: OrbitParticle[] = [];
    for (let ring = 0; ring < 3; ring++) {
      const count = 10 + ring * 8;
      for (let i = 0; i < count; i++) {
        PARTICLES.push({
          angle:      (i / count) * Math.PI * 2,
          ring,
          speed:      (0.003 + Math.random() * 0.006) * (Math.random() < 0.5 ? 1 : -1),
          size:       1.2 + Math.random() * 2.2,
          opacity:    0.4 + Math.random() * 0.6,
          phase:      Math.random() * Math.PI * 2,
          phaseSpeed: 0.03 + Math.random() * 0.04,
        });
      }
    }

    // Spike rotation angle
    let spikeAngle = 0;
    let coronaPulse = 0;
    let animId: number;

    function rgb(r: number, g: number, b: number, a: number) {
      return `rgba(${r},${g},${b},${a})`;
    }

    function drawSpike(
      angle: number,
      length: number,
      width: number,
      [r, g, b]: [number, number, number],
      alpha: number
    ) {
      ctx.save();
      ctx.translate(CX, CY);
      ctx.rotate(angle);

      // Forward spike
      const grad = ctx.createLinearGradient(0, 0, length, 0);
      grad.addColorStop(0,   rgb(r, g, b, alpha));
      grad.addColorStop(0.3, rgb(r, g, b, alpha * 0.5));
      grad.addColorStop(1,   rgb(r, g, b, 0));
      ctx.beginPath();
      ctx.moveTo(0, -width / 2);
      ctx.lineTo(length, 0);
      ctx.lineTo(0,  width / 2);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Backward spike (shorter)
      const grad2 = ctx.createLinearGradient(0, 0, -length * 0.55, 0);
      grad2.addColorStop(0,   rgb(r, g, b, alpha * 0.7));
      grad2.addColorStop(1,   rgb(r, g, b, 0));
      ctx.beginPath();
      ctx.moveTo(0, -width * 0.4);
      ctx.lineTo(-length * 0.55, 0);
      ctx.lineTo(0,  width * 0.4);
      ctx.closePath();
      ctx.fillStyle = grad2;
      ctx.fill();

      ctx.restore();
    }

    function draw() {
      if (!ctx) return;
      const cfg = STATE_CFG[stateRef.current];
      const [r, g, b]   = cfg.rgb;
      const [r2,g2,b2]  = cfg.rgb2;
      const iv = cfg.intensity;

      ctx.clearRect(0, 0, SIZE, SIZE);

      // Update timers
      spikeAngle  += cfg.rotSpeed;
      coronaPulse += 0.04;

      const pulseFactor = 0.85 + Math.sin(coronaPulse) * 0.15;

      // ── Outer corona ─────────────────────────────────────────────────────────
      const coronaR = BASE_R * 1.55 * pulseFactor;
      const corona  = ctx.createRadialGradient(CX, CY, 0, CX, CY, coronaR * 2);
      corona.addColorStop(0,   rgb(r,g,b, 0.18 * iv));
      corona.addColorStop(0.3, rgb(r,g,b, 0.12 * iv));
      corona.addColorStop(0.7, rgb(r,g,b, 0.04 * iv));
      corona.addColorStop(1,   rgb(r,g,b, 0));
      ctx.beginPath();
      ctx.arc(CX, CY, coronaR * 2, 0, Math.PI * 2);
      ctx.fillStyle = corona;
      ctx.fill();

      // ── Diffraction spikes ────────────────────────────────────────────────────
      const spikeL   = BASE_R * cfg.spikeLen;
      const spacing  = (Math.PI * 2) / cfg.spikeCount;
      const secSpacing = spacing / 2;

      // Secondary spikes (dimmer, shorter)
      for (let i = 0; i < cfg.spikeCount; i++) {
        drawSpike(
          spikeAngle + i * spacing + secSpacing,
          spikeL * 0.55,
          4,
          [r2,g2,b2],
          0.35 * iv * pulseFactor
        );
      }

      // Primary spikes (bright)
      for (let i = 0; i < cfg.spikeCount; i++) {
        drawSpike(
          spikeAngle + i * spacing,
          spikeL,
          7,
          [r,g,b],
          0.75 * iv * pulseFactor
        );
      }

      // ── Inner ring ────────────────────────────────────────────────────────────
      const ringR = BASE_R * 0.72 * pulseFactor;
      ctx.beginPath();
      ctx.arc(CX, CY, ringR, 0, Math.PI * 2);
      ctx.strokeStyle = rgb(r, g, b, 0.28 * iv);
      ctx.lineWidth = 1;
      ctx.setLineDash([6, 10]);
      ctx.stroke();
      ctx.setLineDash([]);

      // ── Orbit particles ───────────────────────────────────────────────────────
      const ringRadii = [BASE_R * 0.55, BASE_R * 0.85, BASE_R * 1.15];
      const speedMul  = cfg.orbitSpeed / 0.004; // relative to base

      for (const p of PARTICLES) {
        if (p.ring >= cfg.particleRings) continue;
        p.angle += p.speed * speedMul;
        p.phase += p.phaseSpeed;

        const orbitR = ringRadii[p.ring];
        const px = CX + Math.cos(p.angle) * orbitR;
        const py = CY + Math.sin(p.angle) * orbitR;
        const pulse = (Math.sin(p.phase) + 1) * 0.5;
        const pr    = p.size * (0.6 + pulse * 0.7);
        const alpha = p.opacity * (0.3 + pulse * 0.7) * iv;

        // Glow
        const pg = ctx.createRadialGradient(px, py, 0, px, py, pr * 4);
        pg.addColorStop(0, rgb(r, g, b, alpha * 0.6));
        pg.addColorStop(1, rgb(r, g, b, 0));
        ctx.beginPath();
        ctx.arc(px, py, pr * 4, 0, Math.PI * 2);
        ctx.fillStyle = pg;
        ctx.fill();

        // Dot
        ctx.beginPath();
        ctx.arc(px, py, pr, 0, Math.PI * 2);
        ctx.fillStyle = rgb(255, 240, 255, Math.min(alpha * 1.5, 1));
        ctx.fill();
      }

      // ── Draw connecting lines between nearby orbit particles ──────────────────
      const orbitParticles = PARTICLES.filter((p) => p.ring < cfg.particleRings);
      for (let i = 0; i < orbitParticles.length; i++) {
        const pi = orbitParticles[i];
        const piR = ringRadii[pi.ring];
        const pix = CX + Math.cos(pi.angle) * piR;
        const piy = CY + Math.sin(pi.angle) * piR;
        for (let j = i + 1; j < orbitParticles.length; j++) {
          const pj = orbitParticles[j];
          if (Math.abs(pi.ring - pj.ring) > 1) continue;
          const pjR = ringRadii[pj.ring];
          const pjx = CX + Math.cos(pj.angle) * pjR;
          const pjy = CY + Math.sin(pj.angle) * pjR;
          const dx = pix - pjx, dy = piy - pjy;
          const dist = Math.sqrt(dx*dx + dy*dy);
          const maxD = BASE_R * 0.45;
          if (dist > maxD) continue;
          const lAlpha = (1 - dist / maxD) * 0.22 * iv;
          ctx.beginPath();
          ctx.moveTo(pix, piy);
          ctx.lineTo(pjx, pjy);
          ctx.strokeStyle = rgb(r, g, b, lAlpha);
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }

      // ── Innermost glow core ───────────────────────────────────────────────────
      const coreR = BASE_R * 0.26 * pulseFactor;
      const coreG = ctx.createRadialGradient(CX, CY, 0, CX, CY, coreR);
      coreG.addColorStop(0,   rgb(255, 248, 255, 0.95 * iv));
      coreG.addColorStop(0.25,rgb(r, g, b, 0.85 * iv));
      coreG.addColorStop(0.7, rgb(r2,g2,b2, 0.35 * iv));
      coreG.addColorStop(1,   rgb(r, g, b, 0));
      ctx.beginPath();
      ctx.arc(CX, CY, coreR, 0, Math.PI * 2);
      ctx.fillStyle = coreG;
      ctx.fill();

      // ── Bright star-center point ──────────────────────────────────────────────
      const starG = ctx.createRadialGradient(CX, CY, 0, CX, CY, BASE_R * 0.09);
      starG.addColorStop(0,   `rgba(255,255,255,${0.98 * iv})`);
      starG.addColorStop(0.5, rgb(r, g, b, 0.8 * iv));
      starG.addColorStop(1,   rgb(r, g, b, 0));
      ctx.beginPath();
      ctx.arc(CX, CY, BASE_R * 0.09, 0, Math.PI * 2);
      ctx.fillStyle = starG;
      ctx.fill();

      // ── FAILED: red X ─────────────────────────────────────────────────────────
      if (stateRef.current === "FAILED") {
        ctx.save();
        ctx.translate(CX, CY);
        ctx.strokeStyle = rgb(248,113,113, 0.9);
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        const s = BASE_R * 0.18;
        ctx.beginPath(); ctx.moveTo(-s,-s); ctx.lineTo(s,s); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(s,-s);  ctx.lineTo(-s,s); ctx.stroke();
        ctx.restore();
      }

      // ── COMPLETED: check ──────────────────────────────────────────────────────
      if (stateRef.current === "COMPLETED") {
        ctx.save();
        ctx.translate(CX, CY);
        ctx.strokeStyle = rgb(52,211,153, 0.95);
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        const s = BASE_R * 0.18;
        ctx.beginPath();
        ctx.moveTo(-s, 0);
        ctx.lineTo(-s * 0.2, s * 0.8);
        ctx.lineTo(s, -s * 0.6);
        ctx.stroke();
        ctx.restore();
      }

      // ── WAITING: pause bars ───────────────────────────────────────────────────
      if (stateRef.current === "WAITING_FOR_APPROVAL") {
        ctx.save();
        ctx.translate(CX, CY);
        ctx.fillStyle = rgb(251,191,36, 0.85);
        const h = BASE_R * 0.3, w = BASE_R * 0.08, gap = BASE_R * 0.12;
        ctx.fillRect(-gap - w, -h / 2, w, h);
        ctx.fillRect(gap,      -h / 2, w, h);
        ctx.restore();
      }

      animId = requestAnimationFrame(draw);
    }

    draw();
    return () => cancelAnimationFrame(animId);
  }, []);

  const cfg = STATE_CFG[state];
  const [lr, lg, lb] = cfg.labelRgb;

  return (
    <div className="relative flex flex-col items-center justify-center w-full h-full select-none">
      <canvas
        ref={canvasRef}
        width={320}
        height={320}
        style={{ display: "block" }}
      />
      {/* State label */}
      <div className="absolute bottom-0 left-0 right-0 flex flex-col items-center gap-1 pb-1">
        <span
          className="mono text-[10px] font-medium tracking-[0.2em] transition-colors duration-700"
          style={{ color: `rgb(${lr},${lg},${lb})` }}
        >
          {cfg.label}
        </span>
        <div className="flex items-center gap-1">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full animate-status"
            style={{ background: `rgb(${lr},${lg},${lb})`, boxShadow: `0 0 4px rgb(${lr},${lg},${lb})` }}
          />
          <span className="mono text-[9px]" style={{ color: "var(--text-dim)" }}>LEVI · AIS</span>
        </div>
      </div>
    </div>
  );
}
