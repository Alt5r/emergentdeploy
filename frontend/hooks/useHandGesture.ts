"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  FilesetResolver,
  GestureRecognizer,
  GestureRecognizerResult,
} from "@mediapipe/tasks-vision"

export type GestureType = "Open_Palm" | "Closed_Fist" | "Pointing_Up" | "Victory" | "None"

export interface HandGestureData {
  gesture: GestureType
  confidence: number
  handedness: string
  landmarks?: Array<{ x: number; y: number; z: number }>
}

export interface UseHandGestureOptions {
  enabled?: boolean
  onGestureDetected?: (data: HandGestureData) => void
  minConfidence?: number
  videoElement?: HTMLVideoElement | null
}

export function useHandGesture({
  enabled = true,
  onGestureDetected,
  minConfidence = 0.7,
  videoElement: externalVideoElement,
}: UseHandGestureOptions = {}) {
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentGesture, setCurrentGesture] = useState<HandGestureData | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)

  const recognizerRef = useRef<GestureRecognizer | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const lastGestureTimeRef = useRef<number>(0)

  // Initialize MediaPipe Gesture Recognizer
  useEffect(() => {
    if (!enabled) return

    let isMounted = true

    async function initializeGestureRecognizer() {
      try {
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        )

        const recognizer = await GestureRecognizer.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath:
              "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
            delegate: "GPU",
          },
          runningMode: "VIDEO",
          numHands: 1,
          minHandDetectionConfidence: minConfidence,
          minHandPresenceConfidence: minConfidence,
          minTrackingConfidence: minConfidence,
        })

        if (isMounted) {
          recognizerRef.current = recognizer
          setIsReady(true)
        }
      } catch (err) {
        console.error("Failed to initialize gesture recognizer:", err)
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to initialize")
        }
      }
    }

    initializeGestureRecognizer()

    return () => {
      isMounted = false
      if (recognizerRef.current) {
        recognizerRef.current.close()
        recognizerRef.current = null
      }
    }
  }, [enabled, minConfidence])

  // Initialize camera stream
  const initializeCamera = useCallback(async () => {
    if (!enabled || stream) return

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      })

      setStream(mediaStream)
      
      const video = externalVideoElement || videoRef.current
      if (video) {
        video.srcObject = mediaStream
        await video.play()
      }
    } catch (err) {
      console.error("Failed to access camera:", err)
      setError(err instanceof Error ? err.message : "Failed to access camera")
    }
  }, [enabled, stream, externalVideoElement])

  // Process video frames
  useEffect(() => {
    if (!enabled || !isReady || !recognizerRef.current) return

    const video = externalVideoElement || videoRef.current
    if (!video) return

    let lastVideoTime = -1

    function processFrame() {
      if (!enabled || !recognizerRef.current || !video) return

      const currentTime = video.currentTime
      if (currentTime === lastVideoTime) {
        animationFrameRef.current = requestAnimationFrame(processFrame)
        return
      }
      lastVideoTime = currentTime

      try {
        const result: GestureRecognizerResult = recognizerRef.current.recognizeForVideo(
          video,
          performance.now()
        )

        if (result.gestures && result.gestures.length > 0) {
          const gesture = result.gestures[0][0]
          const handedness = result.handedness[0][0]?.categoryName || "Unknown"
          const landmarks = result.landmarks[0]

          if (gesture && gesture.score >= minConfidence) {
            const gestureData: HandGestureData = {
              gesture: gesture.categoryName as GestureType,
              confidence: gesture.score,
              handedness,
              landmarks: landmarks?.map((lm) => ({ x: lm.x, y: lm.y, z: lm.z })),
            }

            // Throttle gesture updates (max 10 per second)
            const now = performance.now()
            if (now - lastGestureTimeRef.current > 100) {
              setCurrentGesture(gestureData)
              onGestureDetected?.(gestureData)
              lastGestureTimeRef.current = now
            }
          }
        } else {
          // No gesture detected
          const now = performance.now()
          if (now - lastGestureTimeRef.current > 100) {
            setCurrentGesture(null)
            lastGestureTimeRef.current = now
          }
        }
      } catch (err) {
        console.error("Error processing frame:", err)
      }

      animationFrameRef.current = requestAnimationFrame(processFrame)
    }

    // Start processing when video is ready
    if (video.readyState >= 2) {
      processFrame()
    } else {
      video.addEventListener("loadeddata", processFrame)
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      video.removeEventListener("loadeddata", processFrame)
    }
  }, [enabled, isReady, minConfidence, onGestureDetected, externalVideoElement])

  // Cleanup
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [stream])

  return {
    isReady,
    error,
    currentGesture,
    stream,
    videoRef,
    initializeCamera,
  }
}

