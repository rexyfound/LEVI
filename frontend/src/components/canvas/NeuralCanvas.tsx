import { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import * as THREE from 'three';
import { CoreNucleus } from './CoreNucleus';
import { NeuralLattice } from './NeuralLattice';
import { CoreState } from '../../types/events';


interface NeuralCanvasProps {
  state: CoreState;
}

function EnvironmentEffects({ state, mousePos }: { state: CoreState; mousePos: { x: number; y: number } }) {
  const dustRef = useRef<THREE.Points>(null);

  const dustPositions = useRef(() => {
    const count = 300;
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 25;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 25;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 25;
    }
    return pos;
  }).current();

  useFrame((stateCtx, delta) => {
    const camera = stateCtx.camera;
    const targetX = mousePos.x * 0.5;
    const targetY = mousePos.y * 0.5;
    camera.position.x += (targetX - camera.position.x) * delta * 2.0;
    camera.position.y += (targetY - camera.position.y) * delta * 2.0;

    if (dustRef.current) {
      dustRef.current.rotation.y += delta * 0.02;
    }
  });

  return (
    <>
      <fog attach="fog" args={['#040507', 12, 35]} />

      {/* Ambient Volumetric Stardust */}
      <points ref={dustRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[dustPositions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.03}
          color="#38bdf8"
          transparent
          opacity={0.3}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </>
  );
}

export function NeuralCanvas({ state }: NeuralCanvasProps) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: -(e.clientY / window.innerHeight - 0.5) * 2,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="absolute inset-0 w-full h-full pointer-events-auto z-0">
      <Canvas
        camera={{ position: [0, 0, 7.6], fov: 40, near: 0.1, far: 100 }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.0,
        }}
      >
        {/* Balanced Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 5, 5]} intensity={1.5} />
        <Environment preset="night" />

        <EnvironmentEffects state={state} mousePos={mousePos} />

        {/* Dynamic 3D Core */}
        <CoreNucleus state={state} mousePos={mousePos} />

        {/* Dynamic 3D Synaptic Lattice */}
        <NeuralLattice state={state} mousePos={mousePos} />
      </Canvas>

      {/* Interactive Tool Icons Column overlaying the Neural Core right perimeter (matching screenshot) */}
      <div className="absolute right-6 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-10 pointer-events-auto">
        {[
          { icon: '🌐', title: 'Browser Engine' },
          { icon: '🧠', title: 'Neural Core' },
          { icon: '🎯', title: 'Action Tracker' },
          { icon: '🧊', title: 'Memory Indexer' },
          { icon: '📦', title: 'System Storage' },
          { icon: '⚡', title: 'Task Pipeline' },
        ].map((item, idx) => (
          <button
            key={idx}
            title={item.title}
            className="w-9 h-9 rounded-full bg-[#120b24]/70 border border-[#a855f7]/30 hover:border-[#c084fc] flex items-center justify-center text-xs text-[#d8b4fe] backdrop-blur-md transition-all shadow-[0_0_12px_rgba(168,85,247,0.2)] hover:scale-110"
          >
            {item.icon}
          </button>
        ))}
      </div>

      {/* Bottom Processing Progress Bar (matching screenshot) */}
      <div className="absolute bottom-6 left-12 right-12 z-10 pointer-events-none">
        <div className="flex items-center justify-between text-[11px] text-[#a855f7] mb-1 font-mono tracking-wider">
          <span>PROCESSING</span>
          <span>68%</span>
        </div>
        <div className="text-[10px] text-slate-400 font-mono mb-2">Analyzing request and selecting tools...</div>
        <div className="w-full h-1 bg-[#1a0f35] rounded-full overflow-hidden border border-[#a855f7]/20">
          <div className="h-full w-[68%] bg-gradient-to-r from-[#8b5cf6] via-[#c084fc] to-[#e879f9] shadow-[0_0_8px_#c084fc]" />
        </div>
      </div>
    </div>
  );
}



