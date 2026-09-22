import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { CoreState } from '../../types/events';


interface CoreNucleusProps {
  state: CoreState;
  mousePos?: { x: number; y: number };
}

export function CoreNucleus({ state, mousePos }: CoreNucleusProps) {
  const corePointsRef = useRef<THREE.Points>(null);
  const coreLinesRef = useRef<THREE.LineSegments>(null);
  const innerNucleusRef = useRef<THREE.Mesh>(null);
  const outerRing1Ref = useRef<THREE.Mesh>(null);
  const outerRing2Ref = useRef<THREE.Mesh>(null);
  const starGlowRef = useRef<THREE.Points>(null);
  const lightRef = useRef<THREE.PointLight>(null);

  // Deep Violet & State-Based Reactive Color/Animation Configurations
  const getStateConfig = (s: CoreState) => {
    switch (s) {
      case 'RECEIVING':
        return { main: '#38bdf8', bright: '#7dd3fc', inner: '#0284c7', speed: 0.35, pulseFreq: 3.5, light: 4.5 };
      case 'PLANNING':
        return { main: '#a855f7', bright: '#e9d5ff', inner: '#c084fc', speed: 0.45, pulseFreq: 4.0, light: 5.0 };
      case 'EXECUTING':
        return { main: '#c084fc', bright: '#f0abfc', inner: '#e879f9', speed: 0.65, pulseFreq: 5.5, light: 6.0 };
      case 'WAITING_CONFIRMATION':
        return { main: '#f59e0b', bright: '#fde047', inner: '#ef4444', speed: 0.08, pulseFreq: 1.2, light: 3.0 };
      case 'VALIDATING':
        return { main: '#818cf8', bright: '#c7d2fe', inner: '#6366f1', speed: 0.3, pulseFreq: 2.5, light: 4.0 };
      case 'FAILED':
        return { main: '#ef4444', bright: '#fca5a5', inner: '#991b1b', speed: 0.7, pulseFreq: 6.0, light: 6.5 };
      case 'COMPLETED':
        return { main: '#10b981', bright: '#6ee7b7', inner: '#047857', speed: 0.25, pulseFreq: 2.0, light: 4.0 };
      case 'IDLE':
      default:
        return { main: '#8b5cf6', bright: '#c084fc', inner: '#a855f7', speed: 0.12, pulseFreq: 1.8, light: 3.2 };
    }
  };

  const config = getStateConfig(state);
  const mainColor = useRef(new THREE.Color(config.main));
  const brightColor = useRef(new THREE.Color(config.bright));
  const innerColor = useRef(new THREE.Color(config.inner));


  // Generate dense geodesic sphere point cloud & web lattice
  const { positions, linePositions, starPositions } = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(2.0, 4);
    const posAttr = geo.attributes.position;
    const vertexCount = posAttr.count;

    const posArray = new Float32Array(vertexCount * 3);
    const lineList: number[] = [];

    for (let i = 0; i < vertexCount; i++) {
      const x = posAttr.getX(i);
      const y = posAttr.getY(i);
      const z = posAttr.getZ(i);

      posArray[i * 3] = x;
      posArray[i * 3 + 1] = y;
      posArray[i * 3 + 2] = z;
    }

    // Connect vertices within distance threshold for web structure
    for (let i = 0; i < vertexCount; i++) {
      const p1 = new THREE.Vector3(posArray[i * 3], posArray[i * 3 + 1], posArray[i * 3 + 2]);
      for (let j = i + 1; j < vertexCount; j++) {
        const p2 = new THREE.Vector3(posArray[j * 3], posArray[j * 3 + 1], posArray[j * 3 + 2]);
        if (p1.distanceTo(p2) < 0.85) {
          lineList.push(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
        }
      }
    }

    // Extra inner bright star points
    const starCount = 120;
    const starArray = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const r = Math.random() * 1.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      starArray[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      starArray[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      starArray[i * 3 + 2] = r * Math.cos(phi);
    }

    return {
      positions: posArray,
      linePositions: new Float32Array(lineList),
      starPositions: starArray,
    };
  }, []);

  useFrame((stateCtx, delta) => {
    const clock = stateCtx.clock.elapsedTime;
    mainColor.current.lerp(new THREE.Color(config.main), delta * 4.0);
    brightColor.current.lerp(new THREE.Color(config.bright), delta * 4.0);
    innerColor.current.lerp(new THREE.Color(config.inner), delta * 4.0);

    const mx = (mousePos?.x || 0) * 0.15;
    const my = (mousePos?.y || 0) * 0.15;

    // Dynamic Point Light Intensity based on state config
    if (lightRef.current) {
      lightRef.current.color.copy(mainColor.current);
      lightRef.current.intensity = config.light + Math.sin(clock * config.pulseFreq) * 0.8;
    }

    // Core point cloud rotation & pulsing
    if (corePointsRef.current) {
      corePointsRef.current.rotation.y += delta * config.speed;
      corePointsRef.current.rotation.x += delta * (config.speed * 0.5);
      const pulse = 1.0 + Math.sin(clock * config.pulseFreq) * 0.03;
      corePointsRef.current.scale.set(pulse + mx * 0.05, pulse - my * 0.05, pulse);
    }

    if (coreLinesRef.current) {
      coreLinesRef.current.rotation.y += delta * config.speed;
      coreLinesRef.current.rotation.x += delta * (config.speed * 0.5);
      const pulse = 1.0 + Math.sin(clock * config.pulseFreq) * 0.03;
      coreLinesRef.current.scale.set(pulse + mx * 0.05, pulse - my * 0.05, pulse);
    }

    // Inner glowing core nucleus
    if (innerNucleusRef.current) {
      innerNucleusRef.current.rotation.y -= delta * (config.speed * 1.5);
      const nScale = 0.55 + Math.sin(clock * config.pulseFreq * 1.5) * 0.05;
      innerNucleusRef.current.scale.setScalar(nScale);
    }

    // Outer subtle orbital rings
    if (outerRing1Ref.current) {
      outerRing1Ref.current.rotation.z += delta * (config.speed * 0.6);
      outerRing1Ref.current.rotation.x = Math.sin(clock * 0.4) * 0.2;
    }
    if (outerRing2Ref.current) {
      outerRing2Ref.current.rotation.z -= delta * (config.speed * 0.5);
      outerRing2Ref.current.rotation.y = Math.cos(clock * 0.4) * 0.2;
    }

    // Inner star swarm
    if (starGlowRef.current) {
      starGlowRef.current.rotation.y += delta * (config.speed * 0.4);
    }
  });


  return (
    <group position={[0, 0, 0]}>
      {/* Central Point Light */}
      <pointLight ref={lightRef} position={[0, 0, 0]} distance={25} decay={1.5} />

      {/* Center Supernova Light Nucleus */}
      <mesh ref={innerNucleusRef}>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshBasicMaterial
          color={brightColor.current}
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Geodesic Neural Nodes Point Cloud */}
      <points ref={corePointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.065}
          color={brightColor.current}
          transparent
          opacity={0.95}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Geodesic Web Synaptic Lines */}
      <lineSegments ref={coreLinesRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
        </bufferGeometry>
        <lineBasicMaterial
          color={mainColor.current}
          transparent
          opacity={0.35}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>

      {/* Inner Star Swarm Particles */}
      <points ref={starGlowRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[starPositions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.04}
          color={innerColor.current}
          transparent
          opacity={0.8}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Outer Concentric Precision Ring 1 */}
      <mesh ref={outerRing1Ref}>
        <torusGeometry args={[2.5, 0.005, 16, 120]} />
        <meshBasicMaterial
          color={mainColor.current}
          transparent
          opacity={0.3}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Outer Concentric Precision Ring 2 */}
      <mesh ref={outerRing2Ref}>
        <torusGeometry args={[2.8, 0.003, 16, 120]} />
        <meshBasicMaterial
          color={innerColor.current}
          transparent
          opacity={0.2}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Volumetric Purple Ambient Glow */}
      <mesh>
        <sphereGeometry args={[3.2, 32, 32]} />
        <meshBasicMaterial
          color={mainColor.current}
          transparent
          opacity={0.06}
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}










