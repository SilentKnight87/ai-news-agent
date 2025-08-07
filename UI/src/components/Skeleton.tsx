import { cn } from "@/lib/utils"

interface SkeletonProps {
  className?: string
  variant?: "text" | "circular" | "rectangular" | "card"
  width?: string | number
  height?: string | number
  count?: number
}

export default function Skeleton({ 
  className, 
  variant = "rectangular", 
  width, 
  height,
  count = 1 
}: SkeletonProps) {
  const baseClasses = "animate-pulse bg-gray-700"
  
  const variantClasses = {
    text: "rounded h-4",
    circular: "rounded-full",
    rectangular: "rounded-lg",
    card: "rounded-lg"
  }

  const getStyle = () => {
    const style: React.CSSProperties = {}
    if (width) style.width = typeof width === "number" ? `${width}px` : width
    if (height) style.height = typeof height === "number" ? `${height}px` : height
    return style
  }

  if (variant === "card") {
    return (
      <>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className="w-80 flex-shrink-0">
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              {/* Image skeleton */}
              <div className="w-full h-44 bg-gray-700 animate-pulse" />
              
              {/* Content skeleton */}
              <div className="p-4 space-y-3">
                {/* Title */}
                <div className="h-5 bg-gray-700 rounded animate-pulse" />
                <div className="h-5 bg-gray-700 rounded animate-pulse w-3/4" />
                
                {/* Meta */}
                <div className="flex items-center space-x-3">
                  <div className="h-3 w-20 bg-gray-700 rounded animate-pulse" />
                  <div className="h-3 w-16 bg-gray-700 rounded animate-pulse" />
                </div>
                
                {/* Categories */}
                <div className="flex space-x-2">
                  <div className="h-6 w-16 bg-gray-700 rounded-full animate-pulse" />
                  <div className="h-6 w-20 bg-gray-700 rounded-full animate-pulse" />
                  <div className="h-6 w-14 bg-gray-700 rounded-full animate-pulse" />
                </div>
                
                {/* Summary */}
                <div className="space-y-2">
                  <div className="h-3 bg-gray-700 rounded animate-pulse" />
                  <div className="h-3 bg-gray-700 rounded animate-pulse" />
                  <div className="h-3 bg-gray-700 rounded animate-pulse w-5/6" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </>
    )
  }

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={cn(baseClasses, variantClasses[variant], className)}
          style={getStyle()}
        />
      ))}
    </>
  )
}

export function SkeletonRow({ title }: { title?: string }) {
  return (
    <section className="py-6">
      {/* Section Header */}
      <div className="px-4 sm:px-6 lg:px-8 mb-4">
        {title ? (
          <h2 className="text-2xl font-bold text-white">{title}</h2>
        ) : (
          <Skeleton variant="text" width={200} height={32} />
        )}
      </div>

      {/* Cards */}
      <div className="flex space-x-4 overflow-x-auto scrollbar-hide px-4 sm:px-6 lg:px-8 pb-2">
        <Skeleton variant="card" count={5} />
      </div>
    </section>
  )
}