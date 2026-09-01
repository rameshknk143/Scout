"use client";

// PerspectiveGrid -- the animated 3D grid you see drifting in the background
// of the public landing, reused here behind the System Health page so the
// dashboard feels like part of the same world as the marketing site. Pure CSS
// (the @keyframes sv-grid-pan is already in globals.css), zero JS cost.

export default function PerspectiveGrid() {
  return (
    <div aria-hidden className="sv-grid-perspective">
      <div className="sv-grid-plane" />
    </div>
  );
}
