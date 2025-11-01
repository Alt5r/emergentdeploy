"use client"

import { useEffect, useRef, useState } from "react"
import createGlobe, { COBEOptions } from "cobe"
import { useMotionValue, useSpring } from "motion/react"

import { cn } from "@/lib/utils"
import { useHandGesture } from "@/hooks/useHandGesture"
import { useGlobeGestureControl } from "@/hooks/useGlobeGestureControl"
import { HandTrackingOverlay } from "@/components/HandTrackingOverlay"
import { getShelters } from "@/lib/shelters-api"

const MOVEMENT_DAMPING = 1400

const GLOBE_CONFIG: COBEOptions = {
  width: 800,
  height: 800,
  onRender: () => {},
  devicePixelRatio: 2,
  phi: 0,
  theta: 0.3,
  dark: 0,
  diffuse: 0.4,
  mapSamples: 16000,
  mapBrightness: 1.2,
  baseColor: [1, 1, 1],
  markerColor: [0 / 255, 150 / 255, 255 / 255], // Blue for shelters
  glowColor: [1, 1, 1],
  markers: [], // Will be populated from API
}

export function Globe({
  className,
  config = GLOBE_CONFIG,
  enableHandTracking = false,
  showVideoFeed = false,
}: {
  className?: string
  config?: COBEOptions
  enableHandTracking?: boolean
  showVideoFeed?: boolean
}) {
  const phiRef = useRef(0)
  const widthRef = useRef(0)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const pointerInteracting = useRef<number | null>(null)
  const pointerInteractionMovement = useRef(0)

  const [cameraRequested, setCameraRequested] = useState(false)
  const [shelterMarkers, setShelterMarkers] = useState<Array<{ location: [number, number]; size: number }>>([])

  // Fetch shelter data on mount
  useEffect(() => {
    async function loadShelters() {
      try {
        const shelters = await getShelters() // Get all shelters (will show CA when available)
        console.log("Loaded shelters:", shelters)
        const markers = shelters.map(shelter => ({
          location: [shelter.latitude, shelter.longitude] as [number, number],
          size: 0.1 // Larger size so it's visible
        }))
        setShelterMarkers(markers)
        console.log("Shelter markers:", markers)
      } catch (error) {
        console.error("Failed to load shelters:", error)
      }
    }
    loadShelters()
  }, [])

  const r = useMotionValue(0)
  const rs = useSpring(r, {
    mass: 1,
    damping: 30,
    stiffness: 100,
  })

  // Scale/zoom control
  const scale = useMotionValue(1)
  const scaleSpring = useSpring(scale, {
    mass: 0.8,
    damping: 20,
    stiffness: 80,
  })

  // Hand gesture detection
  const {
    isReady: gestureReady,
    error: gestureError,
    currentGesture,
    videoRef,
    initializeCamera,
  } = useHandGesture({
    enabled: enableHandTracking,
    minConfidence: 0.65,
  })

  // Gesture control for globe
  const { handleGesture, autoRotateRef } = useGlobeGestureControl({
    rotationValue: r,
    phiRef,
    scaleValue: scale,
    enabled: enableHandTracking && gestureReady,
    rotationSensitivity: 0.03,
    zoomSensitivity: 0.02,
  })

  // Handle gesture changes
  useEffect(() => {
    if (enableHandTracking && currentGesture) {
      handleGesture(currentGesture)
    }
  }, [currentGesture, enableHandTracking, handleGesture])

  // Request camera access
  const handleRequestCamera = () => {
    setCameraRequested(true)
    initializeCamera()
  }

  // Auto-initialize camera if hand tracking is enabled
  useEffect(() => {
    if (enableHandTracking && !cameraRequested) {
      handleRequestCamera()
    }
  }, [enableHandTracking, cameraRequested])

  // Update container transform based on scale
  const [currentScale, setCurrentScale] = useState(1)
  useEffect(() => {
    const unsubscribe = scaleSpring.on("change", (latest) => {
      setCurrentScale(latest)
    })
    return () => unsubscribe()
  }, [scaleSpring])

  const updatePointerInteraction = (value: number | null) => {
    pointerInteracting.current = value
    if (canvasRef.current) {
      canvasRef.current.style.cursor = value !== null ? "grabbing" : "grab"
    }
  }

  const updateMovement = (clientX: number) => {
    if (pointerInteracting.current !== null) {
      const delta = clientX - pointerInteracting.current
      pointerInteractionMovement.current = delta
      r.set(r.get() + delta / MOVEMENT_DAMPING)
    }
  }

  useEffect(() => {
    const onResize = () => {
      if (canvasRef.current) {
        widthRef.current = canvasRef.current.offsetWidth
      }
    }

    window.addEventListener("resize", onResize)
    onResize()

    const globe = createGlobe(canvasRef.current!, {
      ...config,
      markers: shelterMarkers, // Use shelter markers from API
      width: widthRef.current * 2,
      height: widthRef.current * 2,
      onRender: (state) => {
        // Only auto-rotate if not interacting and auto-rotate is enabled
        if (!pointerInteracting.current && (!enableHandTracking || autoRotateRef.current)) {
          phiRef.current += 0.005
        }
        state.phi = phiRef.current + rs.get()
        state.width = widthRef.current * 2
        state.height = widthRef.current * 2
      },
    })

    setTimeout(() => (canvasRef.current!.style.opacity = "1"), 0)
    return () => {
      globe.destroy()
      window.removeEventListener("resize", onResize)
    }
  }, [rs, config, shelterMarkers])

  return (
    <>
      <div
        className={cn(
          "absolute inset-0 mx-auto aspect-[1/1] w-full max-w-[600px]",
          className
        )}
        style={{
          transform: `scale(${currentScale})`,
          transformOrigin: "center center",
        }}
      >
        <canvas
          className={cn(
            "size-full opacity-0 transition-opacity duration-500 [contain:layout_paint_size]"
          )}
          ref={canvasRef}
          onPointerDown={(e) => {
            pointerInteracting.current = e.clientX
            updatePointerInteraction(e.clientX)
          }}
          onPointerUp={() => updatePointerInteraction(null)}
          onPointerOut={() => updatePointerInteraction(null)}
          onMouseMove={(e) => updateMovement(e.clientX)}
          onTouchMove={(e) =>
            e.touches[0] && updateMovement(e.touches[0].clientX)
          }
        />
      </div>

      {/* Hand tracking overlay - outside scaled container */}
      {enableHandTracking && (
        <HandTrackingOverlay
          gesture={currentGesture}
          isReady={gestureReady}
          error={gestureError}
          videoRef={videoRef}
          onRequestCamera={handleRequestCamera}
          showVideo={showVideoFeed}
        />
      )}
    </>
  )
}
