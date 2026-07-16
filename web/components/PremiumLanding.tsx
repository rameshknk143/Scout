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

// Skeuomorphic Circular Dial Gauge Component
function SkeuomorphicDial() {
  const [score, setScore] = useState(78);
  
  const cycleScore = () => {
    const scores = [45, 62, 78, 89, 95];
    const currentIndex = scores.indexOf(score);
    const nextIndex = (currentIndex + 1) % scores.length;
    setScore(scores[nextIndex]);
  };

  // Maps score (0-100) to rotation angle (-120deg to 120deg)
  const angle = ((score / 100) * 240) - 120;

  return (
    <div className="flex flex-col items-center p-6 rounded-3xl bg-slate-900/30 border-t border-l border-white/10 shadow-[8px_8px_20px_#040609,-8px_-8px_20px_#0e1423] backdrop-blur-xl max-w-xs mx-auto">
      <h4 className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-4 text-center font-mono">
        Opportunity Meter
      </h4>
      
      {/* Skeuomorphic Gauge Plate */}
      <div className="relative w-40 h-40 rounded-full bg-gradient-to-b from-[#161a29] to-[#0a0c14] border-4 border-zinc-700/80 shadow-[inset_4px_4px_8px_rgba(0,0,0,0.8),0_10px_20px_rgba(0,0,0,0.6)] flex items-center justify-center overflow-hidden">
        {/* Chrome Reflection Overlay */}
        <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/5 to-white/10 pointer-events-none rounded-full" />
        
        {/* Scale Markings */}
        <svg className="absolute inset-0 w-full h-full transform -rotate-[210deg]">
          <circle cx="80" cy="80" r="65" stroke="rgba(255,255,255,0.05)" strokeWidth="6" fill="none" strokeDasharray="3 6" />
          <circle cx="80" cy="80" r="65" stroke="#3b82f6" strokeWidth="2" fill="none" strokeDasharray="180 360" strokeDashoffset="90" className="opacity-40" />
        </svg>

        {/* Center Needle */}
        <div 
          className="absolute w-1 h-14 bg-gradient-to-t from-red-600 to-red-400 origin-bottom rounded-full shadow-[0_0_8px_rgba(239,68,68,0.8)] transition-transform duration-700 ease-out"
          style={{ 
            transform: `rotate(${angle}deg)`, 
            bottom: "80px", 
            left: "79px" 
          }}
        />

        {/* Center Metal Cap */}
        <div className="absolute w-7 h-7 rounded-full bg-gradient-to-b from-zinc-400 via-zinc-600 to-zinc-800 border border-zinc-950 shadow-[2px_2px_4px_rgba(0,0,0,0.6),inset_0_1px_1px_rgba(255,255,255,0.4)] flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-zinc-950" />
        </div>

        {/* Digital Readout */}
        <div className="absolute bottom-5 flex flex-col items-center">
          <span className="text-[9px] uppercase font-bold tracking-widest text-zinc-500 font-mono">ASIN SCORE</span>
          <span className="text-lg font-black font-mono text-blue-400 drop-shadow-[0_0_6px_rgba(59,130,246,0.6)]">{score}</span>
        </div>
      </div>

      <button 
        type="button" 
        onClick={cycleScore}
        className="mt-5 w-full bg-gradient-to-b from-zinc-700 via-zinc-800 to-zinc-900 border-t border-white/20 border-b border-black/80 shadow-[0_4px_6px_rgba(0,0,0,0.5)] active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.8)] active:translate-y-[2px] text-zinc-200 hover:text-white font-bold text-[9px] uppercase tracking-widest py-2 rounded-xl transition-all cursor-pointer font-mono"
      >
        ⚡ Cycle Demo ASIN
      </button>
    </div>
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

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-white font-sans selection:bg-blue-600/30 relative overflow-x-hidden">
      {/* 3D Scene Background (Fixed in backdrop) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
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

      {/* Background Decorative Glowing Spheres (Glassmorphism backdrop layer) */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-1/2 right-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px] pointer-events-none z-0" />

      {/* Foreground Content */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Sticky Glass Navbar */}
        <header className="sticky top-0 z-50 w-full bg-[#090d16]/60 backdrop-blur-md border-b border-white/5 py-4 px-6 md:px-12 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔭</span>
            <span className="text-sm font-extrabold tracking-widest text-white font-mono">ScoutVeda</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-zinc-400">
            <button onClick={() => scrollToSection("features")} className="hover:text-white transition-colors cursor-pointer bg-transparent border-0 p-0">Features</button>
            <button onClick={() => scrollToSection("security")} className="hover:text-white transition-colors cursor-pointer bg-transparent border-0 p-0">Security</button>
            <button onClick={() => scrollToSection("tech-stack")} className="hover:text-white transition-colors cursor-pointer bg-transparent border-0 p-0">Tech Stack</button>
          </nav>

          <div>
            <button 
              onClick={() => scrollToSection("signin")} 
              className="bg-gradient-to-b from-zinc-700 via-zinc-800 to-zinc-900 border-t border-white/20 border-b border-black/80 shadow-[0_4px_6px_rgba(0,0,0,0.5)] active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.8)] active:translate-y-[2px] text-white font-bold text-xs px-4 py-2 rounded-lg transition-all cursor-pointer"
            >
              Access App
            </button>
          </div>
        </header>

        {/* Hero Section */}
        <section id="hero" className="flex-1 max-w-7xl mx-auto w-full px-6 md:px-12 py-16 md:py-24 flex flex-col lg:flex-row items-center gap-12 justify-center">
          {/* Hero Left Content */}
          <div className="flex-1 space-y-6 text-left max-w-xl">
            <div className="flex flex-wrap gap-2">
              <span className="text-[10px] font-bold tracking-widest text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full uppercase font-mono">
                🇮🇳 Amazon India
              </span>
              <span className="text-[10px] font-bold tracking-widest text-blue-400 bg-blue-400/10 border border-blue-400/20 px-2.5 py-1 rounded-full uppercase font-mono">
                🇺🇸 Amazon US
              </span>
              <span className="text-[10px] font-bold tracking-widest text-violet-400 bg-violet-400/10 border border-violet-400/20 px-2.5 py-1 rounded-full uppercase font-mono">
                🇬🇧 Amazon UK
              </span>
            </div>

            <motion.h1
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-4xl md:text-5xl font-black tracking-tight text-white leading-[1.1]"
            >
              Product intelligence, <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-amber-400 bg-clip-text text-transparent">refined.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-zinc-400 text-sm leading-relaxed"
            >
              ScoutVeda blends three dimensions of design: Tactile shadow depth, glassmorphism overlays, and physical hardware dials. An advanced sourcing radar for high-volume Amazon resellers.
            </motion.p>

            {/* Interactive Demo Component Grid Row */}
            <div className="flex flex-col sm:flex-row gap-6 pt-4 items-center">
              <div className="flex-1">
                <SkeuomorphicDial />
              </div>
              
              <div className="flex-1 space-y-4">
                <div className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mt-0.5">✔</span>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-200">Daily Bestseller Radar</h4>
                    <p className="text-[11px] text-zinc-500 leading-snug">Track category lists across 31 product branches.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mt-0.5">✔</span>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-200">FBA Fee & Margin Audit</h4>
                    <p className="text-[11px] text-zinc-500 leading-snug">Calculate exact referral, logistics, and GST splits.</p>
                  </div>
                </div>
                <div className="flex items-start gap-2.5">
                  <span className="text-emerald-400 mt-0.5">✔</span>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-200">Keyword Harvester</h4>
                    <p className="text-[11px] text-zinc-500 leading-snug">Harvest search autocomplete terms in real time.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Hero Right - Glass login card with Neumorphic and Skeuomorphic styling */}
          <div id="signin" className="w-full max-w-md shrink-0 py-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.15 }}
              className="p-8 bg-slate-900/35 border-t border-l border-white/10 backdrop-blur-xl rounded-3xl shadow-[8px_8px_20px_#040609,-8px_-8px_20px_#0e1423] relative"
            >
              <div className="absolute -top-3 -right-3 bg-gradient-to-b from-blue-500 to-blue-700 border-t border-blue-300/30 border-b border-black/50 text-white font-mono text-[9px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-md shadow-lg">
                Private Portal
              </div>
              
              <h2 className="text-base font-black mb-6 text-white uppercase tracking-widest text-center font-mono drop-shadow-md">
                🔒 System Sign In
              </h2>
              
              <form action={formAction} className="space-y-6">
                <input type="hidden" name="from" value={from} />
                
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-[9px] font-black text-zinc-400 uppercase tracking-widest font-mono text-center">
                    Enter Access Key
                  </label>
                  
                  {/* Neumorphic Recessed Input Field */}
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    className="w-full bg-slate-950/60 shadow-[inset_4px_4px_8px_rgba(0,0,0,0.9),inset_-4px_-4px_8px_rgba(255,255,255,0.015)] border border-white/5 rounded-xl px-4 py-3.5 text-sm text-white placeholder-zinc-605 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all font-mono text-center"
                    required
                    autoFocus
                  />
                </div>

                {state?.error && (
                  <div className="text-red-400 text-xs border border-red-500/20 bg-red-500/10 px-3 py-2 rounded-lg font-semibold font-mono text-center">
                    {state.error}
                  </div>
                )}

                {/* Skeuomorphic Shiny Blue CTA Button */}
                <button
                  type="submit"
                  disabled={pending}
                  className="w-full bg-gradient-to-b from-blue-500 via-blue-600 to-blue-700 border-t border-blue-300/40 border-b border-black/80 shadow-[0_6px_12px_-2px_rgba(0,0,0,0.6)] hover:from-blue-450 hover:to-blue-650 active:translate-y-[2px] active:shadow-[inset_0_4px_8px_rgba(0,0,0,0.8)] text-white font-black text-xs py-3.5 rounded-xl uppercase tracking-wider transition-all cursor-pointer mt-2"
                >
                  {pending ? "Unlocking Portal..." : "Authorize Access →"}
                </button>
              </form>
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="max-w-7xl mx-auto w-full px-6 md:px-12 py-20 border-t border-white/5 bg-[#090d16]/30 backdrop-blur-[2px]">
          <div className="text-center max-w-xl mx-auto mb-16 space-y-3">
            <h2 className="text-3xl font-extrabold tracking-tight text-white font-sans">Sourcing & Listing Modules</h2>
            <p className="text-xs text-zinc-400 leading-relaxed font-mono uppercase tracking-wider">
              An all-in-one execution system built for Amazon resellers to source accurately and optimize listings.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">📈</div>
              <h3 className="text-sm font-bold text-white mb-2">Trend Radar & Database</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Tracks bestseller categories and aggregates thousands of data snapshots nightly. Quickly spot rank changes and discover rising niche trends.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">🎯</div>
              <h3 className="text-sm font-bold text-white mb-2">Opportunity Finder</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Validate any ASIN against listings standards. Computes listing quality scores, checks competitor review profiles, and grades sourcing viability.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">🔑</div>
              <h3 className="text-sm font-bold text-white mb-2">Keyword Harvester</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                A high-intent tool that queries Amazon autocomplete suggestions recursively (a-z) to discover search traffic. Export directly to CSV.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">💬</div>
              <h3 className="text-sm font-bold text-white mb-2">AI Review Miner</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Extracts real reviews from Amazon mobile endpoints (bypassing blockades) and generates automated AI summaries of product pros and cons.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">💰</div>
              <h3 className="text-sm font-bold text-white mb-2">Profit & FBA Fee Audit</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Precise calculators for FBA Referral fees, closing fees, weight handling, and GST tax splits, giving you absolute clarity on net margins.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 hover:bg-slate-900/45 hover:border-white/15 transition-all group shadow-[6px_6px_16px_rgba(0,0,0,0.5),-6px_-6px_16px_rgba(255,255,255,0.01)] backdrop-blur-sm">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">📦</div>
              <h3 className="text-sm font-bold text-white mb-2">Inventory Planner</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Uses historical run-rate metrics to plan replenishment intervals, estimate lead time buffers, and project stock-out dates.
              </p>
            </div>
          </div>
        </section>

        {/* Security Section */}
        <section id="security" className="max-w-7xl mx-auto w-full px-6 md:px-12 py-20 border-t border-white/5">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1 space-y-4 text-left">
              <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">🔒 Enterprise-Grade Data Security</h2>
              <p className="text-xs text-zinc-400 leading-relaxed font-mono uppercase tracking-wider">
                Your credentials and seller tokens are confidential. ScoutVeda implements robust security policies sitting on top of modern database best practices:
              </p>
              
              <ul className="space-y-3 text-xs text-zinc-300 pt-2">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✔</span> AES-256 Fernet-encrypted credentials at rest.
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✔</span> Encrypted, expiring cookie-based session verification (HMAC).
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✔</span> Anti-bruteforce protection with instant login lockouts.
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✔</span> Real CORS validation middleware gating the APIs.
                </li>
              </ul>
            </div>

            <div className="flex-1 w-full grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Security Card 1 */}
              <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
                <h4 className="text-xs font-bold text-white mb-2">CORS Protection</h4>
                <p className="text-[11px] text-zinc-500 leading-relaxed">Rigid allowlist policies gate Render's endpoint to prevent unauthorized domains from hitting your API.</p>
              </div>
              
              {/* Security Card 2 */}
              <div className="p-6 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
                <h4 className="text-xs font-bold text-white mb-2">HMAC Tokens</h4>
                <p className="text-[11px] text-zinc-500 leading-relaxed">Expiring session tokens secure web requests, preventing replay or hijacking attacks.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Tech Stack Section */}
        <section id="tech-stack" className="max-w-7xl mx-auto w-full px-6 md:px-12 py-16 border-t border-white/5 bg-[#090d16]/20">
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-white tracking-tight">System Infrastructure</h2>
            <p className="text-xs text-zinc-400 mt-2 font-mono uppercase tracking-wider">A robust serverless & microservices architecture that handles high volume operations at near-zero overhead cost.</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="p-5 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white font-mono">Next.js 16</h4>
              <p className="text-[10px] text-zinc-500 mt-1">App router, Server Actions</p>
            </div>
            <div className="p-5 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white font-mono">FastAPI</h4>
              <p className="text-[10px] text-zinc-500 mt-1">Python scraping & math engine</p>
            </div>
            <div className="p-5 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white font-mono">Supabase</h4>
              <p className="text-[10px] text-zinc-500 mt-1">Relational database</p>
            </div>
            <div className="p-5 rounded-2xl bg-slate-900/25 border-t border-l border-white/10 shadow-[6px_6px_16px_rgba(0,0,0,0.5)] backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white font-mono">GitHub Actions</h4>
              <p className="text-[10px] text-zinc-500 mt-1">Nightly scraper runner</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-auto py-8 border-t border-white/5 px-6 md:px-12 bg-[#090d16] relative z-10">
          <div className="max-w-7xl mx-auto w-full flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-[10px] text-zinc-500 font-mono">
              © 2026 KNK Enterprises • Private Reseller OS
            </div>
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-emerald-500 font-bold uppercase font-mono">All Systems Operational</span>
            </div>
            <div className="text-[10px] text-zinc-600 font-mono">
              Version 1.2
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}