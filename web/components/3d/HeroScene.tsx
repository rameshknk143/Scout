"use client";

import { Suspense, useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float, OrbitControls, Environment } from "@react-three/drei";
import * as THREE from "three";

function FloatingAmazonBox() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.15;
      ref.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.3) * 0.1;
      ref.current.position.y = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.15;
    }
  });

  return (
    <Float speed={1.8} rotationIntensity={0.4} floatIntensity={0.3}>
      <mesh ref={ref} castShadow receiveShadow>
        <boxGeometry args={[1.4, 1.4, 1.4]} />
        <meshStandardMaterial
          color="#d29054" /* Cardboard warm box color */
          metalness={0.1}
          roughness={0.65}
          envMapIntensity={0.8}
        />
      </mesh>
    </Float>
  );
}

function FloatingDataCard() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.x = Math.sin(state.clock.getElapsedTime() * 0.35) * 0.4 + 1.8;
      ref.current.rotation.y = Math.cos(state.clock.getElapsedTime() * 0.25) * 0.3;
      ref.current.position.y = Math.cos(state.clock.getElapsedTime() * 0.45) * 0.1 + 0.3;
    }
  });

  return (
    <mesh ref={ref} castShadow receiveShadow position={[1.8, 0.3, 0.5]}>
      <boxGeometry args={[0.7, 0.45, 0.08]} />
      <meshStandardMaterial color="#3b82f6" metalness={0.9} roughness={0.1} />
    </mesh>
  );
}

function FloatingSearchIcon() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.z = Math.cos(state.clock.getElapsedTime() * 0.8) * 0.25;
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.4;
      ref.current.position.y = Math.sin(state.clock.getElapsedTime() * 0.6) * 0.1 + 0.8;
    }
  });

  return (
    <mesh ref={ref} position={[-1.6, 0.8, 0.6]}>
      <torusGeometry args={[0.26, 0.07, 16, 32]} />
      <meshStandardMaterial color="#f59e0b" metalness={0.95} roughness={0.05} />
    </mesh>
  );
}

function Stars() {
  const count = 600;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      pos[idx] = (Math.random() - 0.5) * 40;
      pos[idx + 1] = (Math.random() - 0.5) * 40;
      pos[idx + 2] = (Math.random() - 0.5) * 40;
    }
    return pos;
  }, [count]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial size={0.18} color="#94a3b8" sizeAttenuation opacity={0.35} transparent />
    </points>
  );
}

export default function HeroScene() {
  return (
    <Canvas
      shadows
      camera={{ position: [0, 0, 4.8], fov: 50 }}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={0.65} />
      <directionalLight
        position={[8, 8, 4]}
        intensity={1.2}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />

      <Stars />

      <Suspense fallback={null}>
        <Environment files="/dikhololo_night_1k.hdr" />
        <FloatingAmazonBox />
        <FloatingDataCard />
        <FloatingSearchIcon />
      </Suspense>

      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate
        autoRotateSpeed={0.3}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2}
      />
    </Canvas>
  );
}