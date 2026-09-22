import { useRef, useEffect } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  pulsePhase: number;
  pulseSpeed: number;
  color: 0 | 1 | 2; // 0=violet, 1=cyan, 2=violet-light
}

// Colour palettes
const NODE_RGBA = [
  (a: number) => `rgba(139,92,246,${a})`,
  (a: number) => `rgba(76,201,240,${a})`,
  (a: number) => `rgba(167,139,250,${a})`,
];
const LINE_RGBA = [
  (a: number) => `rgba(139,92,246,${a})`,
  (a: number) => `rgba(76,201,240,${a})`,
  (a: number) => `rgba(120,100,248,${a})`,
];

const COUNT     = 160;   // total nodes — dense enough to cover corners
const MAX_DIST  = 200;   // connection threshold (px)
const MAX_DIST2 = MAX_DIST * MAX_DIST;

export default function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let W = 0, H = 0;
    let nodes: Node[] = [];

    function init() {
      W = canvas!.width  = window.innerWidth;
      H = canvas!.height = window.innerHeight;

      // Seed nodes in a jittered grid that covers the entire canvas including corners
      nodes = [];
      const cols = Math.ceil(Math.sqrt(COUNT * (W / H)));
      const rows = Math.ceil(COUNT / cols);
      const cellW = W / cols;
      const cellH = H / rows;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          if (nodes.length >= COUNT) break;
          const colorIdx = (Math.floor(Math.random() * 10) < 7 ? 0 : Math.random() < 0.5 ? 1 : 2) as 0|1|2;
          nodes.push({
            // Place within cell with jitter — goes right to the edges
            x: c * cellW + Math.random() * cellW,
            y: r * cellH + Math.random() * cellH,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            size: 1.2 + Math.random() * 2.4,
            opacity: 0.45 + Math.random() * 0.55,
            pulsePhase: Math.random() * Math.PI * 2,
            pulseSpeed: 0.008 + Math.random() * 0.022,
            color: colorIdx,
          });
        }
      }
    }

    init();
    window.addEventListener("resize", init);

    // Pre-allocated position cache
    const px = new Float32Array(COUNT);
    const py = new Float32Array(COUNT);

    function draw() {
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);

      // Move nodes — wrap at edges so coverage stays full at all times
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        n.pulsePhase += n.pulseSpeed;
        // Wrap with a small margin so nodes re-enter from the opposite side
        if (n.x < -20)    n.x = W + 20;
        if (n.x > W + 20) n.x = -20;
        if (n.y < -20)    n.y = H + 20;
        if (n.y > H + 20) n.y = -20;
        px[i] = n.x;
        py[i] = n.y;
      }

      const len = nodes.length;

      // ── Draw connections ──────────────────────────────────────────────────────
      for (let i = 0; i < len; i++) {
        for (let j = i + 1; j < len; j++) {
          const dx = px[i] - px[j];
          const dy = py[i] - py[j];
          const d2 = dx * dx + dy * dy;
          if (d2 > MAX_DIST2) continue;

          const dist = Math.sqrt(d2);
          const proximity = 1 - dist / MAX_DIST;
          const ni = nodes[i], nj = nodes[j];
          const pulse = (Math.sin(ni.pulsePhase * 0.6 + nj.pulsePhase * 0.4) + 1) * 0.5;
          // Brighter alpha so lines are clearly visible on dark bg
          const alpha = proximity * 0.65 * (0.4 + pulse * 0.6);

          ctx.beginPath();
          ctx.moveTo(px[i], py[i]);
          ctx.lineTo(px[j], py[j]);
          ctx.strokeStyle = LINE_RGBA[ni.color](alpha);
          ctx.lineWidth   = 0.4 + proximity * 0.9;
          ctx.stroke();
        }
      }

      // ── Draw nodes ────────────────────────────────────────────────────────────
      for (let i = 0; i < len; i++) {
        const n  = nodes[i];
        const x  = px[i], y = py[i];
        const pulse = (Math.sin(n.pulsePhase) + 1) * 0.5;
        const r     = n.size * (0.7 + pulse * 0.6);
        const alpha = n.opacity * (0.35 + pulse * 0.65);
        const cfn   = NODE_RGBA[n.color];

        // Glow halo
        const gr = ctx.createRadialGradient(x, y, 0, x, y, r * 5.5);
        gr.addColorStop(0, cfn(alpha * 0.55));
        gr.addColorStop(1, cfn(0));
        ctx.beginPath();
        ctx.arc(x, y, r * 5.5, 0, Math.PI * 2);
        ctx.fillStyle = gr;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = cfn(Math.min(alpha * 1.4, 1));
        ctx.fill();
      }

      animId = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", init);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0, left: 0,
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: 0,
        display: "block",
      }}
    />
  );
}
