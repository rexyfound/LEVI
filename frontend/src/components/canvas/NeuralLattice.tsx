import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { CoreState } from '../../types/events';

import { useAdaptivePerformance } from '../../hooks/useAdaptivePerformance';

interface NeuralLatticeProps {
  state: CoreState;
  mousePos?: { x: number; y: number };
}

export function NeuralLattice({ state, mousePos }: NeuralLatticeProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const linesRef = useRef<THREE.LineSegments>(null);
  const energyPacketsRef = useRef<THREE.Points>(null);
  const perfTier = useAdaptivePerformance();

  // Initialize organic node physics data (positions, velocities, masses)
  const nodes = useMemo(() => {
    const count = perfTier.nodeCount;
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    const masses = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 2.8 + Math.random() * 4.5;

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);

      vel[i * 3] = (Math.random() - 0.5) * 0.005;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.005;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.005;

      masses[i] = 0.5 + Math.random() * 1.5;
    }

    return { pos, vel, masses, count };
  }, [perfTier.nodeCount]);

  // Energy packet particles traveling across synapses
  const energyPackets = useMemo(() => {
    const packetCount = Math.floor(perfTier.nodeCount * 0.4);
    const pos = new Float32Array(packetCount * 3);
    const targets = new Float32Array(packetCount * 3);
    const progress = new Float32Array(packetCount);

    for (let i = 0; i < packetCount; i++) {
      progress[i] = Math.random();
    }

    return { pos, targets, progress, packetCount };
  }, [perfTier.nodeCount]);

  // Dynamic lines buffer
  const lineGeo = useRef(new THREE.BufferGeometry()).current;
  const linePositionsRef = useRef<Float32Array>(new Float32Array(perfTier.nodeCount * 12));

  useFrame((_, delta) => {
    const { pos, vel, masses, count } = nodes;
    const speedMult = state === 'THINKING' ? 1.8 : state === 'EXECUTING' ? 2.5 : state === 'MEMORY_WRITE' ? 3.0 : 0.8;
    const mx = (mousePos?.x || 0) * 0.02;
    const my = (mousePos?.y || 0) * 0.02;

    const linePosList: number[] = [];

    // Organic Physics Simulation: Inertia, Attraction, Repulsion
    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      
      // Update position with velocity & inertia
      pos[idx] += vel[idx] * speedMult + mx * (1 / masses[i]);
      pos[idx + 1] += vel[idx + 1] * speedMult - my * (1 / masses[i]);
      pos[idx + 2] += vel[idx + 2] * speedMult;

      // Restraining sphere force to keep particles near core lattice
      const dist = Math.sqrt(pos[idx] ** 2 + pos[idx + 1] ** 2 + pos[idx + 2] ** 2);
      if (dist > 7.5 || dist < 2.2) {
        vel[idx] *= -0.9;
        vel[idx + 1] *= -0.9;
        vel[idx + 2] *= -0.9;
      }

      // Connect lines to nearby nodes
      for (let j = i + 1; j < count; j++) {
        const jdx = j * 3;
        const dx = pos[idx] - pos[jdx];
        const dy = pos[idx + 1] - pos[jdx + 1];
        const dz = pos[idx + 2] - pos[jdx + 2];
        const d2 = dx * dx + dy * dy + dz * dz;

        if (d2 < perfTier.maxDistance ** 2) {
          linePosList.push(
            pos[idx], pos[idx + 1], pos[idx + 2],
            pos[jdx], pos[jdx + 1], pos[jdx + 2]
          );
        }
      }
    }

    // Update positions attribute of node points
    if (pointsRef.current) {
      const geo = pointsRef.current.geometry;
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      geo.attributes.position.needsUpdate = true;
      pointsRef.current.rotation.y += delta * 0.05 * speedMult;
    }

    // Update lines geometry
    if (linesRef.current) {
      const lineArray = new Float32Array(linePosList);
      linesRef.current.geometry.setAttribute('position', new THREE.BufferAttribute(lineArray, 3));
      linesRef.current.geometry.attributes.position.needsUpdate = true;
      linesRef.current.rotation.y += delta * 0.05 * speedMult;
    }

    // Update traveling energy packets
    if (energyPacketsRef.current && linePosList.length >= 6) {
      const { pos: pPos, progress, packetCount } = energyPackets;
      for (let k = 0; k < packetCount; k++) {
        progress[k] += delta * 0.4 * speedMult;
        if (progress[k] >= 1.0) progress[k] = 0;

        const lineIndex = Math.floor((k / packetCount) * (linePosList.length / 6)) * 6;
        const x1 = linePosList[lineIndex] || 0;
        const y1 = linePosList[lineIndex + 1] || 0;
        const z1 = linePosList[lineIndex + 2] || 0;
        const x2 = linePosList[lineIndex + 3] || 0;
        const y2 = linePosList[lineIndex + 4] || 0;
        const z2 = linePosList[lineIndex + 5] || 0;

        const t = progress[k];
        pPos[k * 3] = x1 + (x2 - x1) * t;
        pPos[k * 3 + 1] = y1 + (y2 - y1) * t;
        pPos[k * 3 + 2] = z1 + (z2 - z1) * t;
      }
      energyPacketsRef.current.geometry.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      energyPacketsRef.current.geometry.attributes.position.needsUpdate = true;
      energyPacketsRef.current.rotation.y += delta * 0.05 * speedMult;
    }
  });

  const getLatticeColor = (state: CoreState) => {
    switch (state) {
      case 'THINKING': return '#38bdf8';
      case 'EXECUTING': return '#ff6b00';
      case 'MEMORY_WRITE': return '#c084fc';
      case 'AWAITING_APPROVAL': return '#f59e0b';
      case 'ERROR': return '#ef4444';
      case 'COMPLETED': return '#10b981';
      default: return '#06b6d4';
    }
  };

  const currentColor = getLatticeColor(state);

  return (
    <group>
      {/* Neural Node Particles */}
      <points ref={pointsRef}>
        <bufferGeometry />
        <pointsMaterial
          size={perfTier.qualityFactor < 0.8 ? 0.08 : 0.06}
          color={currentColor}
          transparent
          opacity={0.75}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Dynamic Synaptic Connections */}
      <lineSegments ref={linesRef}>
        <bufferGeometry />
        <lineBasicMaterial
          color={currentColor}
          transparent
          opacity={perfTier.qualityFactor < 0.8 ? 0.14 : 0.22}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>

      {/* Animated Traveling Energy Packets */}
      <points ref={energyPacketsRef}>
        <bufferGeometry />
        <pointsMaterial
          size={0.11}
          color="#ffffff"
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

