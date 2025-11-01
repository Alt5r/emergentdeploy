# Hand Tracking Integration for Globe Component

This integration adds MediaPipe-powered hand gesture controls to the Globe component, based on the (https://github.com/snowcodeer/rca-hack).

## Features

- **Touch-free interaction** - Control the globe using hand gestures
- **Real-time gesture recognition** - MediaPipe Tasks Vision for accurate hand tracking
- **Multiple gesture types** - Support for various hand gestures
- **Visual feedback** - On-screen indicators for detected gestures
- **Configurable** - Easy to enable/disable and customize

## Gesture Controls

| Gesture | Action | Description |
|---------|--------|-------------|
| ✊ **Closed Fist** | Zoom In | Gradually zoom into the globe (max 2.5x) |
| ✋ **Open Palm** | Zoom Out | Gradually zoom out from the globe (min 0.5x) |
| ☝️ **Pointing Up** | Rotate | Move your hand left/right to manually rotate the globe |

## Usage

### Basic Usage

```tsx
import { Globe } from "@/components/ui/globe"

export default function MyPage() {
  return (
    <Globe 
      enableHandTracking={true}
      showVideoFeed={false}
    />
  )
}
```

### Props

- `enableHandTracking` (boolean, default: `false`) - Enable hand gesture controls
- `showVideoFeed` (boolean, default: `false`) - Show the camera feed overlay
- `className` (string) - Additional CSS classes
- `config` (COBEOptions) - Globe configuration options

### Demo Page

Visit `/globe-demo` to see the hand tracking in action.

## Architecture

### Components

1. **`useHandGesture` Hook** (`/hooks/useHandGesture.ts`)
   - Initializes MediaPipe Gesture Recognizer
   - Manages camera access and video stream
   - Processes video frames and detects hand gestures
   - Returns current gesture data with confidence scores

2. **`useGlobeGestureControl` Hook** (`/hooks/useGlobeGestureControl.ts`)
   - Maps detected gestures to globe control actions
   - Manages zoom (scale) with smooth spring animations
   - Handles rotation with hand movement tracking
   - Applies smoothing and hysteresis to prevent jitter
   - Reset functionality to return to default view

3. **`HandTrackingOverlay` Component** (`/components/HandTrackingOverlay.tsx`)
   - Visual feedback for gesture detection
   - Status indicators (ready, initializing, error)
   - Gesture guide with descriptions
   - Optional video feed preview

4. **`Globe` Component** (`/components/ui/globe.tsx`)
   - Enhanced with hand tracking integration
   - Maintains backward compatibility (hand tracking is opt-in)
   - Coordinates between gesture detection and COBE rendering

## Requirements

- Modern browser with WebRTC support
- Camera access permission
- Decent lighting for optimal hand detection
- MediaPipe Tasks Vision models (loaded from CDN)

## Browser Compatibility

- ✅ Chrome/Edge 90+
- ✅ Firefox 90+
- ✅ Safari 15+
- ✅ Mobile browsers (iOS Safari, Chrome Android)

## Performance

- Hand detection runs at ~30 FPS
- Minimal impact on globe rendering performance
- GPU-accelerated when available
- Gesture throttling prevents excessive updates

## Troubleshooting

### Camera not working
- Check browser permissions for camera access
- Try HTTPS (camera access requires secure context)
- Check if camera is not in use by another application

### Poor gesture detection
- Ensure good lighting
- Keep hand within camera frame
- Hold gestures for at least 200ms
- Adjust `minConfidence` prop if needed

### High CPU usage
- Disable hand tracking when not needed
- Reduce video resolution (edit `useHandGesture.ts`)
- Close other tabs/applications

## Credits

- Hand tracking system inspired by 
- Powered by [MediaPipe](https://developers.google.com/mediapipe)
- Globe rendering by [COBE](https://github.com/shuding/cobe)

## License

Same as the parent project.

