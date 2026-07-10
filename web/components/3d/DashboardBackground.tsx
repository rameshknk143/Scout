"use client";

import { Suspense, useRef, useMemo, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function DriftingParticles() {
  const points = useRef<THREE.Points>(null!);
  const count = 400;

  useFrame((state) => {
    if (points.current) {
      points.current.rotation.y = state.clock.getElapsedTime() * 0.008;
      points.current.rotation.x = state.clock.getElapsedTime() * 0.004;
    }
  });

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      pos[idx] = (Math.random() - 0.5) * 45;
      pos[idx + 1] = (Math.random() - 0.5) * 45;
      pos[idx + 2] = (Math.random() - 0.5) * 45;
    }
    return pos;
  }, [count]);

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.2}
        color="#a1a1aa"
        sizeAttenuation
        opacity={0.12}
        transparent
      />
    </points>
  );
}

function FloatingRing() {
  const ref = useRef<THREE.Mesh>(null!);
  
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.x = state.clock.getElapsedTime() * 0.02;
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.03;
    }
  });

  return (
    <mesh ref={ref} position={[3, -2, -8]}>
      <torusGeometry args={[3, 0.04, 8, 48]} />
      <meshBasicMaterial color="#ffffff" opacity={0.015} transparent wireframe />
    </mesh>
  );
}

export default function Dashboard3DBackground() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 -z-10 pointer-events-none w-screen h-screen">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 60 }}
        style={{ width: "100%", height: "100%" }}
      >
        <ambientLight intensity={0.2} />
        <Suspense fallback={null}>
          <DriftingParticles />
          <FloatingRing />
        </Suspense>
      </Canvas>
    </div>
  );
}
