"use client"

import { useRef } from "react"
import { MotionValue } from "motion/react"
import { HandGestureData, GestureType } from "./useHandGesture"

export interface GlobeGestureControlOptions {
  rotationValue: MotionValue<number>
  phiRef: React.MutableRefObject<number>
  scaleValue: MotionValue<number>
  enabled?: boolean
  rotationSensitivity?: number
  zoomSensitivity?: number
}

export function useGlobeGestureControl({
  rotationValue,
  phiRef,
  scaleValue,
  enabled = true,
  rotationSensitivity = 0.03,
  zoomSensitivity = 0.02,
}: GlobeGestureControlOptions) {
  const lastGestureRef = useRef<GestureType>("None")
  const gestureStartTimeRef = useRef<number>(0)
  const gestureStartXRef = useRef<number>(0)
  const gestureStartYRef = useRef<number>(0)
  const isGesturingRef = useRef(false)
  const autoRotateRef = useRef(true)

  const handleGesture = (data: HandGestureData | null) => {
    if (!enabled || !data) {
      isGesturingRef.current = false
      autoRotateRef.current = true
      return
    }

    const { gesture, landmarks } = data
    const now = performance.now()

    // Detect gesture changes
    if (gesture !== lastGestureRef.current) {
      lastGestureRef.current = gesture
      gestureStartTimeRef.current = now
      
      if (landmarks && landmarks.length > 0) {
        // Use wrist position (landmark 0) as reference
        gestureStartXRef.current = landmarks[0].x
        gestureStartYRef.current = landmarks[0].y
      }
    }

    // Gesture must be held for at least 200ms to avoid false triggers
    const gestureDuration = now - gestureStartTimeRef.current
    if (gestureDuration < 200) return

    switch (gesture) {
      case "Closed_Fist": {
        // Zoom in - increase scale
        isGesturingRef.current = true
        autoRotateRef.current = false
        
        const currentScale = scaleValue.get()
        const targetScale = Math.min(currentScale + zoomSensitivity, 2.5) // Max zoom 2.5x
        scaleValue.set(targetScale)
        break
      }

      case "Open_Palm": {
        // Zoom out - decrease scale
        isGesturingRef.current = true
        autoRotateRef.current = false
        
        const currentScale = scaleValue.get()
        const targetScale = Math.max(currentScale - zoomSensitivity, 0.5) // Min zoom 0.5x
        scaleValue.set(targetScale)
        break
      }

      case "Pointing_Up": {
        // Rotate - track hand movement left/right
        isGesturingRef.current = true
        autoRotateRef.current = false
        
        if (landmarks && landmarks.length > 0) {
          const currentX = landmarks[0].x
          const deltaX = currentX - gestureStartXRef.current
          
          // Apply horizontal rotation based on hand movement (inverted)
          const rotationDelta = -deltaX * rotationSensitivity * 5
          rotationValue.set(rotationValue.get() + rotationDelta)
          
          // Update reference position
          gestureStartXRef.current = currentX
        }
        break
      }

      case "None":
      default: {
        isGesturingRef.current = false
        autoRotateRef.current = true
        break
      }
    }
  }

  return {
    handleGesture,
    isGesturingRef,
    autoRotateRef,
  }
}

