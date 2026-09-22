import { useState, useRef } from 'react';
import { useFrame } from '@react-three/fiber';

export interface PerformanceTier {
  nodeCount: number;
  dpr: number;
  enableWireframe: boolean;
  maxDistance: number;
  qualityFactor: number;
}

export function useAdaptivePerformance() {
  const [tier, setTier] = useState<PerformanceTier>({
    nodeCount: 100,
    dpr: 1.5,
    enableWireframe: false,
    maxDistance: 2.2,
    qualityFactor: 1.0,
  });

  const frames = useRef(0);
  const prevTime = useRef(performance.now());

  useFrame(() => {
    frames.current++;
    const time = performance.now();

    // Evaluate FPS every 2 seconds
    if (time >= prevTime.current + 2000) {
      const fps = (frames.current * 1000) / (time - prevTime.current);
      frames.current = 0;
      prevTime.current = time;

      // Gracefully adjust rendering performance tier
      if (fps < 40 && tier.qualityFactor > 0.5) {
        setTier({
          nodeCount: 50,
          dpr: 1.0,
          enableWireframe: false,
          maxDistance: 1.8,
          qualityFactor: 0.5,
        });
      } else if (fps >= 55 && tier.qualityFactor < 1.0) {
        setTier({
          nodeCount: 110,
          dpr: 1.5,
          enableWireframe: false,
          maxDistance: 2.2,
          qualityFactor: 1.0,
        });
      }
    }
  });

  return tier;
}
