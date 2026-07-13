"use client";

import { Suspense, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float, OrbitControls, Environment, SpotLight } from "@react-three/drei";
import * as THREE from "three";

function FloatingAmazonBox() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.3;
      ref.current.position.y = Math.sin(state.clock.getElapsedTime() * 0.8) * 0.2;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
      <mesh ref={ref} castShadow receiveShadow>
        <boxGeometry args={[1.5, 1.5, 1.5]} />
        <meshStandardMaterial
          color="#ffffff"
          metalness={0.8}
          roughness={0.2}
          envMapIntensity={1}
        />
      </mesh>
    </Float>
  );
}

function FloatingDataCard() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.x = Math.sin(state.clock.getElapsedTime() * 0.3) * 0.5;
      ref.current.rotation.y = Math.cos(state.clock.getElapsedTime() * 0.2) * 0.2;
    }
  });

  return (
    <mesh ref={ref} castShadow receiveShadow position={[2, 0.5, 0]}>
      <boxGeometry args={[0.8, 0.5, 0.1]} />
      <meshStandardMaterial color="#27272a" metalness={0.8} roughness={0.15} />
    </mesh>
  );
}

function FloatingSearchIcon() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.z = Math.cos(state.clock.getElapsedTime() * 1.2) * 0.3;
      ref.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.1;
    }
  });

  return (
    <mesh ref={ref} position={[-2, 1.2, 0.5]}>
      <torusGeometry args={[0.3, 0.08, 16, 32]} />
      <meshStandardMaterial color="#3f3f46" metalness={0.7} roughness={0.2} />
    </mesh>
  );
}

function Stars() {
  const { viewport } = useThree();
  const count = 500;
  const positions = useRef<Float32Array>(new Float32Array(count * 3));

  useFrame(() => {
    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      if (!positions.current) continue;
      positions.current[idx] = positions.current[idx] || (Math.random() - 0.5) * 50;
      positions.current[idx + 1] = positions.current[idx + 1] || (Math.random() - 0.5) * 50;
      positions.current[idx + 2] = positions.current[idx + 2] || (Math.random() - 0.5) * 50;
    }
  });

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions.current, 3]}
        />
      </bufferGeometry>
      <pointsMaterial size={0.3} color="#a1a1aa" sizeAttenuation opacity={0.4} transparent />
    </points>
  );
}

export default function HeroScene() {
  return (
    <Canvas
      shadows
      camera={{ position: [0, 0, 5], fov: 60 }}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={0.5} />
      <directionalLight
        position={[10, 10, 5]}
        intensity={1}
        castShadow
        shadow-mapSize={[1024, 1024]}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />

      <Stars />

      <spotLight
        position={[5, 10, 5]}
        angle={0.3}
        penumbra={1}
        intensity={2}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />

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
        autoRotateSpeed={0.5}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2}
      />
    </Canvas>
  );
}