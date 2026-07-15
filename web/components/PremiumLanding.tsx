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
      ref.current.position.y = Math.sin(state.clock.getElapsedTime() * 0.4) * 0.2 - 0.6;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.3}>
      <mesh ref={ref} position={[-2.2, -0.6, 0.5]}>
        <boxGeometry args={[1.0, 0.35, 0.2]} />
        <meshStandardMaterial color="#f59e0b" metalness={0.95} roughness={0.05} />
      </mesh>
    </Float>
  );
}

function FloatingData() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.x = Math.sin(state.clock.getElapsedTime() * 0.2) * 0.4 + 2.2;
      ref.current.rotation.y = Math.cos(state.clock.getElapsedTime() * 0.15) * 0.15;
    }
  });

  return (
    <mesh ref={ref} position={[2.2, 0.8, 0.5]}>
      <cylinderGeometry args={[0.18, 0.18, 0.35, 32]} />
      <meshStandardMaterial color="#3b82f6" metalness={0.8} roughness={0.15} />
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
    <mesh ref={ref} position={[-2.0, 1.2, 0.5]}>
      <coneGeometry args={[0.25, 0.7, 4]} />
      <meshStandardMaterial color="#ef4444" metalness={0.8} roughness={0.1} />
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
    <div className="min-h-screen bg-[#090d16] relative overflow-hidden flex items-center justify-center p-4">
      {/* 3D Scene Background */}
      <div className="absolute inset-0 z-0">
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
              <Environment files="/studio_small_03_1k.hdr" />
              <FloatingASIN />
              <FloatingData />
              <FloatingChart />
              <BackgroundStars />
            </Suspense>
          </Canvas>
        )}
      </div>

      {/* Floating Center Glass Login Card */}
      <div className="w-full max-w-md relative z-10 flex flex-col items-center">
        {/* Top Header */}
        <div className="flex items-center gap-2 mb-6 px-3 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
          <span className="text-xl">🔭</span>
          <span className="text-sm font-bold tracking-widest text-white font-mono">ScoutVeda</span>
        </div>

        {/* Center Card */}
        <div className="w-full">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6 text-center"
          >
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3 text-white">
              Product intelligence, refined.
            </h1>
            <p className="text-zinc-400 text-xs leading-relaxed max-w-sm mx-auto">
              Log in to access your personal global Amazon intelligence radar across India, USA, and UK.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="glass-panel p-8 bg-slate-950/60 border border-white/10 backdrop-blur-xl shadow-2xl rounded-2xl"
          >
            <h2 className="text-base font-bold mb-5 text-white uppercase tracking-wider text-center font-sans">Sign In</h2>
            <form action={formAction} className="space-y-4">
              <input type="hidden" name="from" value={from} />
              
              <div className="space-y-1.5">
                <label htmlFor="password" className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  className="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all font-mono text-center"
                  required
                  autoFocus
                />
              </div>

              {state?.error && (
                <div className="text-red-400 text-xs border border-red-500/20 bg-red-500/10 px-3 py-2 rounded-lg font-semibold font-mono text-center">
                  {state.error}
                </div>
              )}

              <button
                type="submit"
                disabled={pending}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs py-3 rounded-xl uppercase tracking-wider transition-all shadow-lg hover:shadow-blue-500/20 disabled:opacity-50 cursor-pointer mt-2"
              >
                {pending ? "Signing In..." : "Sign In →"}
              </button>
            </form>
          </motion.div>
        </div>

        {/* Footer */}
        <div className="text-[10px] text-zinc-600 font-mono mt-8 text-center">
          <p>Version 1.2 • © 2026 KNK Enterprises</p>
        </div>
      </div>
    </div>
  );
}