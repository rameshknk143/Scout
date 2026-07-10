"use client";

import { motion } from "framer-motion";
import { useState, useRef, useMemo, useEffect, Suspense, useActionState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Environment } from "@react-three/drei";
import * as THREE from "three";
import { login } from "@/lib/auth-actions";

function FloatingASIN() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y += 0.006;
      ref.current.position.y = Math.sin(state.clock.getElapsedTime() * 0.4) * 0.2;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.3}>
      <mesh ref={ref} position={[0, 0, 0]}>
        <boxGeometry args={[1.0, 0.35, 0.2]} />
        <meshStandardMaterial color="#ffffff" metalness={0.9} roughness={0.08} />
      </mesh>
    </Float>
  );
}

function FloatingData() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.x = Math.sin(state.clock.getElapsedTime() * 0.2) * 0.4 + 2;
      ref.current.rotation.y = Math.cos(state.clock.getElapsedTime() * 0.15) * 0.15;
    }
  });

  return (
    <mesh ref={ref} position={[2, 0.5, 0.5]}>
      <cylinderGeometry args={[0.18, 0.18, 0.35, 32]} />
      <meshStandardMaterial color="#27272a" metalness={0.8} roughness={0.15} />
    </mesh>
  );
}

function FloatingChart() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(state.clock.getElapsedTime() * 0.6) * 0.03);
    }
  });

  return (
    <mesh ref={ref} position={[-1.8, 0.8, 0.5]}>
      <coneGeometry args={[0.25, 0.7, 4]} />
      <meshStandardMaterial color="#3f3f46" metalness={0.7} roughness={0.2} />
    </mesh>
  );
}

function BackgroundStars() {
  const points = useRef<THREE.Points>(null!);
  const count = 1200;

  useFrame((state) => {
    if (points.current) {
      points.current.rotation.y += 0.0002;
      points.current.rotation.x += 0.0001;
    }
  });

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      pos[idx] = (Math.random() - 0.5) * 80;
      pos[idx + 1] = (Math.random() - 0.5) * 80;
      pos[idx + 2] = (Math.random() - 0.5) * 80;
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
      <pointsMaterial size={0.35} color="#71717a" sizeAttenuation opacity={0.22} transparent />
    </points>
  );
}

interface PremiumLandingProps {
  from: string;
}

export default function PremiumLanding({ from }: PremiumLandingProps) {
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const [mounted, setMounted] = useState(false);
  const [state, formAction, pending] = useActionState(login, undefined);

  useEffect(() => {
    setMounted(true);
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX((e.clientX / window.innerWidth) * 2 - 1);
      setMouseY(-(e.clientY / window.innerHeight) * 2 + 1);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-bg relative overflow-hidden flex flex-col md:flex-row">
      {/* 3D Scene Left Side (Hidden on Mobile) */}
      <div className="hidden md:block md:w-1/2 h-full absolute inset-0 md:relative z-10 border-r border-white/5">
        {mounted && (
          <Canvas
            shadows
            camera={{ position: [0, 0, 5.5], fov: 50 }}
            style={{ width: "100%", height: "100%" }}
          >
            <ambientLight intensity={0.9} />
            <directionalLight
              position={[8 + mouseX * 4, 8 + mouseY * 4, 8]}
              intensity={1.5}
              castShadow
            />
            <Suspense fallback={null}>
              <Environment preset="studio" />
              <FloatingASIN />
              <FloatingData />
              <FloatingChart />
              <BackgroundStars />
            </Suspense>
          </Canvas>
        )}
      </div>

      {/* Content Right Side */}
      <div className="w-full md:w-1/2 min-h-screen relative z-20 flex flex-col justify-between px-6 py-12 md:px-16 md:py-20 bg-bg-elevated/80 backdrop-blur-md md:bg-transparent">
        {/* Top Header */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔭</span>
          <span className="text-xl font-bold tracking-tight text-text">SCOUT</span>
        </div>

        {/* Center Card */}
        <div className="max-w-md w-full mx-auto my-auto py-8">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8"
          >
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 text-text">
              Product intelligence, refined.
            </h1>
            <p className="text-muted text-sm leading-relaxed">
              Log in to access your personal Amazon India reseller radar. Keep track of competitors, analyze listings, and scout next-gen opportunities.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="glass-panel p-8"
          >
            <h2 className="text-lg font-semibold mb-6 text-text">Sign In</h2>
            <form action={formAction} className="space-y-4">
              <input type="hidden" name="from" value={from} />
              
              <div>
                <label htmlFor="password" className="block text-xs text-muted mb-1.5 font-medium">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Enter password"
                  className="input py-2.5 text-text"
                  required
                  autoFocus
                />
              </div>

              {state?.error && (
                <div className="text-red text-xs mt-2 border border-red/20 bg-red-soft px-3 py-2 rounded-lg">
                  {state.error}
                </div>
              )}

              <button
                type="submit"
                disabled={pending}
                className="w-full btn-primary py-2.5 mt-2 disabled:opacity-50"
              >
                {pending ? "Signing In..." : "Sign In"}
              </button>
            </form>
          </motion.div>
        </div>

        {/* Footer */}
        <div className="text-xs text-muted/60 mt-8">
          <p>Version 1.0 • © 2026 KNK Enterprises</p>
        </div>
      </div>
    </div>
  );
}