"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useGLTF, Html } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import HeroScene from "./3d/HeroScene";

const PremiumHero = () => {
  const [scrollY, setScrollY] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <section
      ref={heroRef}
      className="relative h-screen w-full overflow-hidden"
    >
      <div className="absolute inset-0 z-0">
        <Canvas
          shadows
          camera={{ position: [0, 0, 5], fov: 60 }}
          style={{ width: "100%", height: "100%" }}
        >
          <ambientLight intensity={0.4} />
          <directionalLight
            position={[10, 10, 5]}
            intensity={1}
            castShadow
          />
          <HeroScene />
        </Canvas>
      </div>

      <motion.div
        className="relative z-10 flex flex-col items-center justify-center h-full"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        <motion.h1
          className="text-6xl md:text-8xl font-bold mb-6"
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          style={{
            background: "linear-gradient(90deg, #f5a623, #34d399)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            filter: "drop-shadow(0 0 30px rgba(245, 166, 35, 0.3))",
          }}
        >
          Scout
        </motion.h1>
        <motion.p
          className="text-xl text-muted mb-8 max-w-2xl text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
        >
          Personal product-intelligence radar for Amazon India sellers.
          Discover winning products, track trends, and make data-driven decisions.
        </motion.p>
        <motion.a
          href="/login"
          className="px-8 py-4 bg-amber text-black font-bold rounded-full shadow-lg hover:shadow-amber/50 transition-all duration-300"
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
        >
          Get Started
        </motion.a>
      </motion.div>

      <motion.div
        className="absolute bottom-10 left-1/2 -translate-x-1/2 z-10"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="w-6 h-10 bg-amber/50 rounded-full flex justify-center">
          <div className="w-1.5 h-3 bg-amber rounded-full mt-2" />
        </div>
      </motion.div>
    </section>
  );
};

export default PremiumHero;