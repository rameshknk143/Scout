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

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-white font-sans selection:bg-blue-600/30 relative">
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
              className="bg-white/5 border border-white/10 hover:bg-white/10 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all cursor-pointer"
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
              ScoutVeda is a private, data-driven sourcing intelligence platform built specifically for Amazon resellers. Monitor category bestsellers, analyze competitor health, and project product profits with precision.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="grid grid-cols-2 gap-4 pt-2"
            >
              <div className="flex items-start gap-2.5">
                <span className="text-emerald-400 mt-0.5">✔</span>
                <div>
                  <h4 className="text-xs font-bold text-zinc-200">Daily Category Snapshots</h4>
                  <p className="text-[11px] text-zinc-500 leading-snug">Track bestsellers across 30+ product lines.</p>
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
              <div className="flex items-start gap-2.5">
                <span className="text-emerald-400 mt-0.5">✔</span>
                <div>
                  <h4 className="text-xs font-bold text-zinc-200">AI Review Mining</h4>
                  <p className="text-[11px] text-zinc-500 leading-snug">Extract real reviews from mobile pages automatically.</p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Hero Right - Glass login card */}
          <div id="signin" className="w-full max-w-md shrink-0 py-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.15 }}
              className="p-8 bg-slate-950/70 border border-white/10 backdrop-blur-xl shadow-2xl rounded-2xl relative"
            >
              <div className="absolute -top-3 -right-3 bg-blue-600 text-white font-mono text-[9px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-md shadow-lg">
                Private Portal
              </div>
              <h2 className="text-base font-bold mb-5 text-white uppercase tracking-wider text-center font-sans">Sign In</h2>
              <form action={formAction} className="space-y-4">
                <input type="hidden" name="from" value={from} />
                
                <div className="space-y-1.5">
                  <label htmlFor="password" className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    Enter System Password
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
                  {pending ? "Signing In..." : "Access Dashboard →"}
                </button>
              </form>
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="max-w-7xl mx-auto w-full px-6 md:px-12 py-20 border-t border-white/5 bg-[#090d16]/30 backdrop-blur-[2px]">
          <div className="text-center max-w-xl mx-auto mb-16 space-y-3">
            <h2 className="text-3xl font-extrabold tracking-tight text-white">Sourcing & Listing Modules</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              An all-in-one execution system built for Amazon resellers to source accurately and optimize listings.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">📈</div>
              <h3 className="text-sm font-bold text-white mb-2">Trend Radar & Database</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Tracks bestseller categories and aggregates thousands of data snapshots nightly. Quickly spot rank changes and discover rising niche trends.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">🎯</div>
              <h3 className="text-sm font-bold text-white mb-2">Opportunity Finder</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Validate any ASIN against listings standards. Computes listing quality scores, checks competitor review profiles, and grades sourcing viability.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">🔑</div>
              <h3 className="text-sm font-bold text-white mb-2">Keyword Harvester</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                A high-intent tool that queries Amazon autocomplete suggestions recursively (a-z) to discover search traffic. Export directly to CSV.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">💬</div>
              <h3 className="text-sm font-bold text-white mb-2">AI Review Miner</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Extracts real reviews from Amazon mobile endpoints (bypassing blockades) and generates automated AI summaries of product pros and cons.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
              <div className="text-2xl mb-4 group-hover:scale-110 transition-transform w-fit">💰</div>
              <h3 className="text-sm font-bold text-white mb-2">Profit & FBA Fee Audit</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Precise calculators for FBA Referral fees, closing fees, weight handling, and GST tax splits, giving you absolute clarity on net margins.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-xl bg-slate-950/40 border border-white/5 hover:border-white/10 hover:bg-slate-950/60 transition-all group">
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
              <p className="text-xs text-zinc-400 leading-relaxed">
                Your credentials and seller tokens are confidential. ScoutVeda implements robust security policies sitting on top of modern database best practices:
              </p>
              <ul className="space-y-2 text-xs text-zinc-300">
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

            <div className="flex-1 w-full grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-5 rounded-lg bg-slate-950/40 border border-white/5">
                <h4 className="text-xs font-bold text-white mb-1">CORS Protection</h4>
                <p className="text-[11px] text-zinc-500">Rigid allowlist policies gate Render's endpoint to prevent unauthorized domains from hitting your API.</p>
              </div>
              <div className="p-5 rounded-lg bg-slate-950/40 border border-white/5">
                <h4 className="text-xs font-bold text-white mb-1">HMAC Tokens</h4>
                <p className="text-[11px] text-zinc-500">Expiring session tokens secure web requests, preventing replay or hijacking attacks.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Tech Stack Section */}
        <section id="tech-stack" className="max-w-7xl mx-auto w-full px-6 md:px-12 py-16 border-t border-white/5 bg-[#090d16]/20">
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-white tracking-tight">System Infrastructure</h2>
            <p className="text-xs text-zinc-400 mt-2">A robust serverless & microservices architecture that handles high volume operations at near-zero overhead cost.</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="p-4 rounded-lg bg-slate-950/20 border border-white/5">
              <h4 className="text-xs font-bold text-white font-mono">Next.js 16</h4>
              <p className="text-[10px] text-zinc-500 mt-1">App router, Server Actions</p>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/20 border border-white/5">
              <h4 className="text-xs font-bold text-white font-mono">FastAPI</h4>
              <p className="text-[10px] text-zinc-500 mt-1">Python scraping & math engine</p>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/20 border border-white/5">
              <h4 className="text-xs font-bold text-white font-mono">Supabase</h4>
              <p className="text-[10px] text-zinc-500 mt-1">Relational database</p>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/20 border border-white/5">
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