"use client"

export default function Aurora() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Soft conic gradients for an AI glow (original palette) */}
      <div className="absolute -top-40 -left-40 h-[60vh] w-[60vw] rounded-full blur-3xl opacity-30 bg-[conic-gradient(at_top_left,_#7dd3fc,_#a78bfa,_#34d399)]" />
      <div className="absolute top-10 right-[-10%] h-[50vh] w-[40vw] rounded-full blur-3xl opacity-20 bg-[conic-gradient(at_bottom_right,_#f472b6,_#60a5fa,_#22c55e)]" />
      {/* Very subtle vignette to focus center */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_40%,_rgba(0,0,0,0.35))]" />
    </div>
  )
}


