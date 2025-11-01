"use client"

import * as React from "react"

interface SliderProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  label?: string
}

export function Slider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  label,
}: SliderProps) {
  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <div className="flex justify-between text-xs text-white/70">
          <span>{label}</span>
          <span>{value.toFixed(2)}</span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-white/20 accent-blue-500"
      />
    </div>
  )
}

