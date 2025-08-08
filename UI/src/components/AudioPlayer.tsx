'use client'

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { formatDuration } from '@/lib/utils'

interface AudioPlayerProps {
  audioUrl: string
  title?: string
  duration?: number
  variant?: 'full' | 'mini'
  onClose?: () => void
}

export function AudioPlayer({ 
  audioUrl, 
  title = 'AI News Digest', 
  duration = 0,
  variant = 'full',
  onClose 
}: AudioPlayerProps) {
  const reduce = useReducedMotion()
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [totalDuration, setTotalDuration] = useState(duration)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime)
    const handleLoadedMetadata = () => setTotalDuration(audio.duration)
    const handleEnded = () => setIsPlaying(false)

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [])

  const togglePlay = () => {
    if (!audioRef.current) return
    
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const skip = (seconds: number) => {
    if (!audioRef.current) return
    audioRef.current.currentTime = Math.max(0, Math.min(totalDuration, audioRef.current.currentTime + seconds))
  }

  const toggleMute = () => {
    if (!audioRef.current) return
    audioRef.current.muted = !isMuted
    setIsMuted(!isMuted)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value)
    setVolume(vol)
    if (audioRef.current) {
      audioRef.current.volume = vol
    }
  }

  const changePlaybackRate = () => {
    const rates = [0.5, 0.75, 1, 1.25, 1.5, 2]
    const currentIndex = rates.indexOf(playbackRate)
    const nextIndex = (currentIndex + 1) % rates.length
    const newRate = rates[nextIndex]
    setPlaybackRate(newRate)
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate
    }
  }

  if (variant === 'mini') {
    return (
      <div className="flex items-center space-x-3 bg-gray-900 rounded-lg p-3">
        <audio ref={audioRef} src={audioUrl} />
        <button
          onClick={togglePlay}
          className="p-2 bg-white text-black rounded-full hover:bg-gray-200 transition-colors"
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <div className="flex-1">
          <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-white"
              style={{ width: `${(currentTime / totalDuration) * 100}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
        </div>
        <span className="text-xs text-gray-400">
          {formatDuration(Math.floor(currentTime))}
        </span>
      </div>
    )
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={reduce ? undefined : { y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={reduce ? undefined : { y: 100, opacity: 0 }}
        className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 z-50"
      >
        <audio ref={audioRef} src={audioUrl} />
        
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-6">
            {/* Play Controls */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => skip(-10)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Skip back 10s"
              >
                <SkipBack size={20} />
              </button>
              
              <button
                onClick={togglePlay}
                className="p-3 bg-white text-black rounded-full hover:bg-gray-200 transition-colors"
              >
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>
              
              <button
                onClick={() => skip(10)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Skip forward 10s"
              >
                <SkipForward size={20} />
              </button>
            </div>

            {/* Progress Bar */}
            <div className="flex-1 flex items-center space-x-3">
              <span className="text-sm text-gray-400 w-12">
                {formatDuration(Math.floor(currentTime))}
              </span>
              
              <input
                type="range"
                min={0}
                max={totalDuration}
                value={currentTime}
                onChange={handleSeek}
                className="flex-1 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 
                  [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white 
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
              />
              
              <span className="text-sm text-gray-400 w-12">
                {formatDuration(Math.floor(totalDuration))}
              </span>
            </div>

            {/* Title */}
            <div className="hidden md:block">
              <p className="text-white font-medium">{title}</p>
              <p className="text-sm text-gray-400">AI Generated Summary</p>
            </div>

            {/* Volume & Speed Controls */}
            <div className="flex items-center space-x-3">
              <button
                onClick={changePlaybackRate}
                className="px-2 py-1 text-sm text-gray-400 hover:text-white transition-colors"
              >
                {playbackRate}x
              </button>
              
              <button
                onClick={toggleMute}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
              
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={volume}
                onChange={handleVolumeChange}
                className="w-20 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 
                  [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white 
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
              />
            </div>

            {/* Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                ×
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}