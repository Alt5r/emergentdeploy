"use client"

import React from "react"
import { HandGestureData } from "@/hooks/useHandGesture"

interface HandTrackingOverlayProps {
  gesture: HandGestureData | null
  isReady: boolean
  error: string | null
  videoRef: React.RefObject<HTMLVideoElement>
  onRequestCamera?: () => void
  showVideo?: boolean
}

const gestureEmojis: Record<string, string> = {
  Open_Palm: "✋",
  Closed_Fist: "✊",
  Pointing_Up: "☝️",
  Victory: "✌️",
  None: "👋",
}

const gestureDescriptions: Record<string, string> = {
  Open_Palm: "Zoom Out",
  Closed_Fist: "Zoom In",
  Pointing_Up: "Rotate Left/Right",
  Victory: "Rotate Up/Down",
  None: "No gesture detected",
}

export function HandTrackingOverlay({
  gesture,
  isReady,
  error,
  videoRef,
  onRequestCamera,
  showVideo = false,
}: HandTrackingOverlayProps) {
  return (
    <div className="pointer-events-none fixed inset-0 z-[9999]">
      {/* Video feed (hidden but processing) */}
      <video
        ref={videoRef}
        className={showVideo ? "absolute right-4 top-4 h-40 w-auto rounded-lg border-2 border-white/20 shadow-lg" : "hidden"}
        playsInline
        muted
      />

      {/* Status indicator */}
      <div className="absolute left-4 top-4 space-y-2">
        {/* Ready indicator */}
        <div className="flex items-center gap-2 rounded-lg bg-black/50 px-3 py-2 text-sm text-white backdrop-blur-sm">
          <div
            className={`h-2 w-2 rounded-full ${
              isReady ? "bg-green-500" : "bg-yellow-500"
            } animate-pulse`}
          />
          <span>{isReady ? "Hand Tracking Active" : "Initializing..."}</span>
        </div>

        {/* Error message */}
        {error && (
          <div className="rounded-lg bg-red-500/80 px-3 py-2 text-sm text-white backdrop-blur-sm">
            {error}
          </div>
        )}

        {/* Camera permission request */}
        {!error && !isReady && onRequestCamera && (
          <button
            onClick={onRequestCamera}
            className="pointer-events-auto rounded-lg bg-blue-500 px-3 py-2 text-sm text-white transition hover:bg-blue-600"
          >
            Enable Camera
          </button>
        )}
      </div>

      {/* Gesture indicator */}
      {gesture && (
        <div className="absolute left-4 top-24 animate-in fade-in slide-in-from-left-4 duration-200">
          <div className="rounded-lg bg-black/70 px-4 py-3 text-white backdrop-blur-md">
            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {gestureEmojis[gesture.gesture] || "👋"}
              </span>
              <div>
                <div className="text-sm font-semibold">
                  {gesture.gesture.replace(/_/g, " ")}
                </div>
                <div className="text-xs text-white/70">
                  {gestureDescriptions[gesture.gesture]}
                </div>
                <div className="mt-1 text-xs text-white/50">
                  Confidence: {(gesture.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gesture guide */}
      <div className="absolute bottom-4 left-4 right-4">
        <details className="pointer-events-auto group">
          <summary className="cursor-pointer rounded-lg bg-black/50 px-4 py-2 text-sm text-white backdrop-blur-sm transition hover:bg-black/60">
            <span className="font-semibold">Gesture Controls</span>
            <span className="ml-2 text-white/60 group-open:hidden">
              (click to expand)
            </span>
          </summary>
          <div className="mt-2 rounded-lg bg-black/70 p-4 text-white backdrop-blur-md">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center gap-3">
                <span className="text-2xl">✊</span>
                <div className="text-xs">
                  <div className="font-semibold">Closed Fist</div>
                  <div className="text-white/70">Zoom In</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl">✋</span>
                <div className="text-xs">
                  <div className="font-semibold">Open Palm</div>
                  <div className="text-white/70">Zoom Out</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl">☝️</span>
                <div className="text-xs">
                  <div className="font-semibold">Point Up</div>
                  <div className="text-white/70">Rotate left/right</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl">✌️</span>
                <div className="text-xs">
                  <div className="font-semibold">Two Fingers</div>
                  <div className="text-white/70">Rotate up/down</div>
                </div>
              </div>
            </div>
          </div>
        </details>
      </div>
    </div>
  )
}

