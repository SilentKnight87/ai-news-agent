"use client"

export default function Aurora() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Soft conic gradients using brand palette */}
      <div className="absolute -top-40 -left-40 h-[60vh] w-[60vw] rounded-full blur-3xl opacity-25 bg-[conic-gradient(at_top_left,_var(--citrine),_var(--fulvous),_var(--turkey-red))]" />
      <div className="absolute top-10 right-[-10%] h-[50vh] w-[40vw] rounded-full blur-3xl opacity-20 bg-[conic-gradient(at_bottom_right,_var(--rosewood),_var(--black-bean),_var(--fulvous))]" />
      {/* Very subtle vignette to focus center */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_45%,_rgba(0,0,0,0.4))]" />
    </div>
  )
}


