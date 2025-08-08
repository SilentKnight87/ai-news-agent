"use client"

import { useRef, useState, useEffect } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ContentRowProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  id?: string
}

export default function ContentRow({ title, subtitle, children, id }: ContentRowProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [showLeftArrow, setShowLeftArrow] = useState(false)
  const [showRightArrow, setShowRightArrow] = useState(true)
  const [isHovered, setIsHovered] = useState(false)
  const reduce = useReducedMotion()

  const checkScrollPosition = () => {
    if (!scrollContainerRef.current) return

    const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current
    setShowLeftArrow(scrollLeft > 0)
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10)
  }

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    checkScrollPosition()
    container.addEventListener("scroll", checkScrollPosition)

    return () => {
      container.removeEventListener("scroll", checkScrollPosition)
    }
  }, [children])

  const scroll = (direction: "left" | "right") => {
    if (!scrollContainerRef.current) return

    const scrollAmount = scrollContainerRef.current.clientWidth * 0.8
    const currentScroll = scrollContainerRef.current.scrollLeft
    const targetScroll = direction === "left" 
      ? currentScroll - scrollAmount 
      : currentScroll + scrollAmount

    scrollContainerRef.current.scrollTo({
      left: targetScroll,
      behavior: "smooth"
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      scroll("left")
    } else if (e.key === "ArrowRight") {
      scroll("right")
    }
  }

  return (
    <section 
      id={id} 
      className="relative py-6"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="region"
      aria-label={title}
      data-testid="content-row"
    >
      {/* Section Header - Origin UI Style */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 mb-6">
        <div className="flex items-baseline gap-3">
          <h2 className="text-2xl font-bold text-white tracking-tight">{title}</h2>
          {subtitle && (
            <p className="text-sm text-gray-500 font-medium">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Content Container */}
      <div className="relative group">
        {/* Left Arrow */}
        <AnimatePresence>
          {isHovered && showLeftArrow && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reduce ? 0 : 0.2 }}
              onClick={() => scroll("left")}
              className={cn(
                "absolute left-0 top-0 bottom-0 z-20 w-16",
                "bg-gradient-to-r from-black via-black/80 to-transparent",
                "flex items-center justify-center",
                "hover:from-black hover:via-black/90",
                "transition-all duration-300"
              )}
              aria-label="Scroll left"
            >
              <div className="p-2 rounded-full bg-gray-800/80 hover:bg-gray-700 transition-colors">
                <ChevronLeft className="w-6 h-6 text-white" />
              </div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Right Arrow */}
        <AnimatePresence>
          {isHovered && showRightArrow && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reduce ? 0 : 0.2 }}
              onClick={() => scroll("right")}
              className={cn(
                "absolute right-0 top-0 bottom-0 z-20 w-16",
                "bg-gradient-to-l from-black via-black/80 to-transparent",
                "flex items-center justify-center",
                "hover:from-black hover:via-black/90",
                "transition-all duration-300"
              )}
              aria-label="Scroll right"
            >
              <div className="p-2 rounded-full bg-gray-800/80 hover:bg-gray-700 transition-colors">
                <ChevronRight className="w-6 h-6 text-white" />
              </div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Scrollable Content */}
        <div className="overflow-hidden">
          <div
            ref={scrollContainerRef}
            className={cn(
              "flex gap-4 overflow-x-auto scrollbar-hide",
              "container mx-auto px-4 sm:px-6 lg:px-8 pb-4",
              "scroll-smooth snap-x snap-mandatory"
            )}
            style={{
              scrollSnapType: "x mandatory",
              scrollPaddingLeft: "32px",
              scrollPaddingRight: "32px"
            }}
          >
            {children}
          </div>
        </div>
      </div>
    </section>
  )
}