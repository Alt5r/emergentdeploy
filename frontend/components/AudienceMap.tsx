"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import mapboxgl, { Map, Marker, LngLatBounds, FillExtrusionLayer } from "mapbox-gl";
import type { FeatureCollection, Feature, Point } from "geojson";
import "mapbox-gl/dist/mapbox-gl.css";
import UnifiedPinSidebar, { transformMarketAnalysisToStats } from "./UnifiedPinSidebar";
import { useHandGesture } from "@/hooks/useHandGesture";
import { HandTrackingOverlay } from "./HandTrackingOverlay";
import { Slider } from "@/components/ui/slider";
import { getShelters } from "@/lib/shelters-api";

/** ---------- Types ---------- */
type AudienceProps = {
  name: string;
  area_code?: string;
  borough?: string;
  country?: string;
  description?: string;
  target_fit?: string;
  weight?: number;
  display_name?: string;
};

type AudienceFeature = Feature<Point, AudienceProps>;
type AudienceCollection = FeatureCollection<Point, AudienceProps>;

type AudienceMapProps = {
  /** Optional Mapbox token override (else fallback below) */
  token?: string;
  /** Initial Mapbox style URL (defaults to LIGHT_STYLE = "standard" globe) */
  initialStyle?: string;
  /** Show the light/dark toggle button */
  enableThemeToggle?: boolean;
  /** Container style/class */
  style?: React.CSSProperties;
  className?: string;
  /** Toggle flags for different overlays */
  showVCs?: boolean;
  showCompetitors?: boolean;
  showDemographics?: boolean;
  showCofounders?: boolean;
  /** Data from API calls */
  competitorsData?: unknown;
  vcsData?: unknown;
  cofoundersData?: unknown;
  demographicsData?: unknown;
  marketAnalysisData?: unknown;
  /** Enable hand tracking controls */
  enableHandTracking?: boolean;
  /** Show video feed for hand tracking */
  showVideoFeed?: boolean;
};

/** ---------- Styles ---------- */
/** Light = original globe look */
const LIGHT_STYLE = "mapbox://styles/mapbox/standard";
/** Dark theme you like */
const DARK_STYLE = "mapbox://styles/mapbox/dark-v11";
/** Satellite view */
const SATELLITE_STYLE = "mapbox://styles/mapbox/satellite-streets-v12";
/** Pure satellite (no labels) */
const SATELLITE_PURE = "mapbox://styles/mapbox/satellite-v9";

/** Default initial style */
const DEFAULT_STYLE = SATELLITE_STYLE;

/** Dev token fallback — replace with your env if you prefer */
const envToken =
  "pk.eyJ1IjoiYWR3aXRoYW5zIiwiYSI6ImNtZ3Y0ejF1ajBna3gya3NlOGxlM2dvaHQifQ.Nm-Nyqb3OLpB1cpZCzvTIw";

/** =======================================================================
 * AudienceMap
 * ======================================================================= */
export default function AudienceMap({
  token,
  competitorsData,
  vcsData,
  cofoundersData,
  demographicsData,
  marketAnalysisData,
  initialStyle = DEFAULT_STYLE,
  enableThemeToggle = false,
  style,
  className,
  showVCs = true,
  showCompetitors = true,
  showDemographics = true,
  showCofounders = true,
  enableHandTracking = false,
  showVideoFeed = false,
}: AudienceMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const vcMarkersRef = useRef<Marker[]>([]);
  const competitorMarkersRef = useRef<Marker[]>([]);
  const cofounderMarkersRef = useRef<Marker[]>([]);
  const shelterMarkersRef = useRef<Marker[]>([]);
  const [styleUrl, setStyleUrl] = useState<string>(initialStyle);
  const [heatmapData, setHeatmapData] = useState<AudienceCollection | null>(null);
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [selectedPinData, setSelectedPinData] = useState<unknown>(null);
  const [showStyleSelector, setShowStyleSelector] = useState(false);
  
  // Hand tracking state
  const [cameraRequested, setCameraRequested] = useState(false);
  const [rotationSensitivity, setRotationSensitivity] = useState(0.5);
  const [zoomSensitivity, setZoomSensitivity] = useState(0.05);
  const [showSensitivityControls, setShowSensitivityControls] = useState(false);
  const lastGestureRef = useRef<string>("None");
  const gestureStartXRef = useRef<number>(0);
  const gestureStartYRef = useRef<number>(0);

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
  });

  /** Handle pin click to show sidebar */
  const handlePinClick = useCallback((pinData: unknown) => {
    setSelectedPinData(pinData);
    setSidebarVisible(true);
  }, []);

  /** Handle sidebar close */
  const handleSidebarClose = useCallback(() => {
    setSidebarVisible(false);
    setSelectedPinData(null);
  }, []);

  /** Request camera access */
  const handleRequestCamera = useCallback(() => {
    setCameraRequested(true);
    initializeCamera();
  }, [initializeCamera]);

  /** Auto-initialize camera if hand tracking is enabled */
  useEffect(() => {
    if (enableHandTracking && !cameraRequested) {
      handleRequestCamera();
    }
  }, [enableHandTracking, cameraRequested, handleRequestCamera]);

  /** Handle hand gestures for map control */
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !enableHandTracking || !gestureReady || !currentGesture) return;

    const { gesture, landmarks } = currentGesture;

    // Detect gesture changes
    if (gesture !== lastGestureRef.current) {
      lastGestureRef.current = gesture;
      if (landmarks && landmarks.length > 0) {
        gestureStartXRef.current = landmarks[0].x;
        gestureStartYRef.current = landmarks[0].y;
      }
    }

    switch (gesture) {
      case "Closed_Fist": {
        // Zoom in
        const currentZoom = map.getZoom();
        map.easeTo({ zoom: currentZoom + zoomSensitivity, duration: 100 });
        break;
      }

      case "Open_Palm": {
        // Zoom out
        const currentZoom = map.getZoom();
        map.easeTo({ zoom: currentZoom - zoomSensitivity, duration: 100 });
        break;
      }

      case "Pointing_Up": {
        // Rotate - track hand movement left/right (spin globe on its axis)
        if (landmarks && landmarks.length > 0) {
          const currentX = landmarks[0].x;
          const deltaX = currentX - gestureStartXRef.current;
          
          // Apply horizontal rotation by changing longitude (inverted)
          const rotationDelta = -deltaX * rotationSensitivity * 100;
          const currentCenter = map.getCenter();
          const newLng = currentCenter.lng + rotationDelta;
          
          map.easeTo({ 
            center: [newLng, currentCenter.lat],
            duration: 100 
          });
          
          // Update reference position
          gestureStartXRef.current = currentX;
        }
        break;
      }

      case "Victory": {
        // Two fingers - vertical rotation (up/down)
        if (landmarks && landmarks.length > 0) {
          const currentY = landmarks[0].y;
          const deltaY = currentY - gestureStartYRef.current;
          
          // Apply vertical rotation by changing latitude (inverted)
          const rotationDelta = -deltaY * rotationSensitivity * 80;
          const currentCenter = map.getCenter();
          const newLat = Math.max(-85, Math.min(85, currentCenter.lat + rotationDelta)); // Clamp to valid range
          
          map.easeTo({ 
            center: [currentCenter.lng, newLat],
            duration: 100 
          });
          
          // Update reference position
          gestureStartYRef.current = currentY;
        }
        break;
      }
    }
  }, [currentGesture, enableHandTracking, gestureReady, rotationSensitivity, zoomSensitivity]);

  /** Offset coordinates to prevent overlapping markers with different patterns for each type */
  const offsetDuplicateCoordinates = (lat: number, lng: number, markerType: 'vc' | 'competitor' | 'cofounder' = 'vc') => {
    const BASE_OFFSET = 0.03; // Base offset in degrees (~33 meters)

    // Different offset patterns for each marker type to ensure they don't overlap
    const offsetPatterns = {
      vc: { lat: 0, lng: 0 }, // VCs stay at original position
      competitor: { lat: BASE_OFFSET, lng: BASE_OFFSET }, // Competitors offset northeast
      cofounder: { lat: -BASE_OFFSET, lng: BASE_OFFSET }, // Cofounders offset northwest
    };

    const pattern = offsetPatterns[markerType];

    // Add a small random variation to prevent exact overlaps within same type
    const randomVariation = (Math.random() - 0.5) * (BASE_OFFSET * 0.3);

    return [
      lng + pattern.lng + randomVariation,
      lat + pattern.lat + randomVariation
    ];
  };

  /** Load demographics data and update map */
  const loadDemographicsData = useCallback((data: AudienceCollection, showDemographicsFlag: boolean, marketAnalysis: unknown, handlePinClickFn: (pinData: unknown) => void) => {
    const map = mapRef.current;
    if (!map) return;

    // Store data for heatmap
    setHeatmapData(data);

    // Fit bounds / center
    const coords = data.features.map((f) => f.geometry.coordinates);
    if (coords.length > 1) {
      const bounds = new LngLatBounds(coords[0] as [number, number], coords[0] as [number, number]);
      coords.forEach((c) => bounds.extend(c as [number, number]));
      map.fitBounds(bounds, { padding: 100, duration: 1200 });
    } else if (coords.length === 1) {
      map.setCenter(coords[0] as [number, number]);
      map.setZoom(10);
    }

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add heatmap if demographics enabled
    if (showDemographicsFlag) {
      // Remove existing heatmap first
      if (map.getLayer("audience-heatmap-layer")) {
        map.removeLayer("audience-heatmap-layer");
      }
      if (map.getSource("audience-heatmap")) {
        map.removeSource("audience-heatmap");
      }

      // Add heatmap source
      map.addSource("audience-heatmap", {
        type: "geojson",
        data: data,
      });

      // Add heatmap layer
      if (!map.getLayer("audience-heatmap-layer")) {
        map.addLayer({
          id: "audience-heatmap-layer",
          type: "heatmap",
          source: "audience-heatmap",
          maxzoom: 15,
          paint: {
            "heatmap-weight": [
              "interpolate",
              ["linear"],
              ["get", "weight"],
              0,
              0,
              1,
              1,
            ],
            "heatmap-intensity": [
              "interpolate",
              ["linear"],
              ["zoom"],
              0,
              1,
              15,
              3,
            ],
            "heatmap-color": [
              "interpolate",
              ["linear"],
              ["heatmap-density"],
              0,
              "rgba(0, 0, 255, 0)",
              0.1,
              "rgb(0, 0, 255)",
              0.3,
              "rgb(0, 255, 0)",
              0.5,
              "rgb(255, 255, 0)",
              0.7,
              "rgb(255, 165, 0)",
              1,
              "rgb(255, 0, 0)",
            ],
            "heatmap-radius": [
              "interpolate",
              ["linear"],
              ["zoom"],
              0,
              20,
              15,
              60,
            ],
            "heatmap-opacity": 0.6,
          },
        });

        // Add cursor pointer for clickable heatmap
        map.getCanvas().style.cursor = "pointer";

        // Add click interactions for heatmap
        map.on("click", "audience-heatmap-layer", (e) => {
          e.preventDefault();
          e.originalEvent.stopPropagation();
          if (e.features && e.features.length > 0) {
            const feature = e.features[0] as unknown as AudienceFeature;
            // Convert heatmap feature to pin data format
            const heatmapPinData = {
              type: 'audience',
              name: feature.properties?.name || 'Audience Member',
              location: feature.properties?.display_name || feature.properties?.area_code || 'Unknown Location',
              description: feature.properties?.description,
              target_fit: feature.properties?.target_fit,
              weight: feature.properties?.weight || 1,
              coordinates: {
                latitude: feature.geometry.coordinates[1],
                longitude: feature.geometry.coordinates[0]
              },
              marketStats: marketAnalysis ? transformMarketAnalysisToStats(marketAnalysis) : undefined
            };
            handlePinClickFn(heatmapPinData);
          }
        });
      }
    }
  }, []);

  /** Add heatmap layer for audience data */
  const addHeatmapLayer = useCallback((marketAnalysis: unknown, handlePinClickFn: (pinData: unknown) => void) => {
    const map = mapRef.current;
    if (!map || !heatmapData || !map.getSource("audience-heatmap")) return;

    if (!map.getLayer("audience-heatmap-layer")) {
      map.addLayer({
        id: "audience-heatmap-layer",
        type: "heatmap",
        source: "audience-heatmap",
        maxzoom: 15,
        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["get", "weight"],
            0,
            0,
            1,
            1,
          ],
          "heatmap-intensity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0,
            1,
            15,
            3,
          ],
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(0, 0, 255, 0)",
            0.1,
            "rgb(0, 0, 255)",
            0.3,
            "rgb(0, 255, 0)",
            0.5,
            "rgb(255, 255, 0)",
            0.7,
            "rgb(255, 165, 0)",
            1,
            "rgb(255, 0, 0)",
          ],
          "heatmap-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0,
            20,
            15,
            60,
          ],
          "heatmap-opacity": 0.6,
        },
      });

      // Add cursor pointer for clickable heatmap
      map.getCanvas().style.cursor = "pointer";

      // Add click interactions for heatmap
      map.on("click", "audience-heatmap-layer", (e) => {
        e.preventDefault();
        e.originalEvent.stopPropagation();
        if (e.features && e.features.length > 0) {
          const feature = e.features[0] as unknown as AudienceFeature;
          // Convert heatmap feature to pin data format
          const heatmapPinData = {
            type: 'audience',
            name: feature.properties?.name || 'Audience Member',
            location: feature.properties?.display_name || feature.properties?.area_code || 'Unknown Location',
            description: feature.properties?.description,
            target_fit: feature.properties?.target_fit,
            weight: feature.properties?.weight || 1,
            coordinates: {
              latitude: feature.geometry.coordinates[1],
              longitude: feature.geometry.coordinates[0]
            },
            marketStats: marketAnalysis ? transformMarketAnalysisToStats(marketAnalysis) : undefined
          };
          handlePinClickFn(heatmapPinData);
        }
      });
    }
  }, [heatmapData]);

  /** Remove heatmap layer */
  const removeHeatmapLayer = useCallback(() => {
    const map = mapRef.current;
    if (!map) return;

    if (map.getLayer("audience-heatmap-layer")) {
      map.removeLayer("audience-heatmap-layer");
    }
    if (map.getSource("audience-heatmap")) {
      map.removeSource("audience-heatmap");
    }
  }, []);

  /** Initialize the map ONCE */
  useEffect(() => {
    const MAPBOX_TOKEN = token ?? envToken ?? "";
    if (!MAPBOX_TOKEN) {
      console.error("Mapbox token missing. Pass the 'token' prop.");
      return;
    }
    if (!containerRef.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [0, 15],
      zoom: 1.2,
      pitch: 0,
      bearing: 0,
      antialias: true,
      attributionControl: false,
      logoPosition: 'bottom-right',
      trackResize: true,
      collectResourceTiming: false, 
    });
    mapRef.current = map;

    /** Keep globe projection whenever styles load/swap */
    const ensureGlobeProjection = () => {
      // If you want globe for both light and dark, keep 'globe' always:
      map.setProjection("globe");
    };

    /** Safely add 3D buildings only for styles that expose 'composite' (e.g., light/dark/streets) */
    const add3dBuildingsIfAvailable = () => {
      const styleObj = map.getStyle();
      const hasComposite = !!styleObj?.sources?.["composite"];
      if (!hasComposite) return; // Mapbox "standard" doesn't expose 'composite'; skip to avoid errors

      const labelLayerId = (styleObj.layers || []).find(
        (l: { type?: string; layout?: Record<string, unknown> }) => l.type === "symbol" && l.layout?.["text-field"]
      )?.id;

      if (!map.getLayer("add-3d-buildings")) {
        const extrusionLayer: FillExtrusionLayer = {
          id: "add-3d-buildings",
          type: "fill-extrusion",
          source: "composite",
          "source-layer": "building",
          filter: ["==", "extrude", "true"],
          minzoom: 15,
          paint: {
            "fill-extrusion-color": "#aaa",
            "fill-extrusion-height": [
              "interpolate",
              ["linear"],
              ["zoom"],
              15,
              0,
              15.05,
              ["get", "height"],
            ],
            "fill-extrusion-base": [
              "interpolate",
              ["linear"],
              ["zoom"],
              15,
              0,
              15.05,
              ["get", "min_height"],
            ],
            "fill-extrusion-opacity": 0.6,
          },
        };
        map.addLayer(extrusionLayer, labelLayerId);
      }
    };


    /** When a style is (re)loaded, keep globe + optional 3D buildings, and reattach markers */
    map.on("style.load", () => {
      ensureGlobeProjection();       // <- keep the globe look
      add3dBuildingsIfAvailable();   // <- only adds on styles that support it
      markersRef.current.forEach((m) => m.addTo(map));
      // Re-add heatmap if demographics enabled and data exists
      if (showDemographics && heatmapData) {
        addHeatmapLayer(marketAnalysisData, handlePinClick);
      }
    });

    /** First-time data load */
    map.on("load", async () => {
      try {
        ensureGlobeProjection(); // make sure initial style starts as globe too

        // If demographics data is available, load it immediately
        if (demographicsData) {
          loadDemographicsData(demographicsData as AudienceCollection, showDemographics, marketAnalysisData, handlePinClick);
        }
      } catch (err) {
        console.error("Error in map load:", err);
      }
    });

    /** Cleanup on unmount */
    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      vcMarkersRef.current.forEach((m) => m.remove());
      vcMarkersRef.current = [];
      competitorMarkersRef.current.forEach((m) => m.remove());
      competitorMarkersRef.current = [];
      cofounderMarkersRef.current.forEach((m) => m.remove());
      cofounderMarkersRef.current = [];
      removeHeatmapLayer();
      map.remove();
      mapRef.current = null;
    };
    // init once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Handle VC toggle - display VCs as pins */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing VC markers
    vcMarkersRef.current.forEach((m) => m.remove());
    vcMarkersRef.current = [];

    if (!showVCs || !vcsData) return;

    // Use data from props
    const data = vcsData;
    console.log("Displaying VCs on map:", data);

    try {

      // Add VC markers to the map
      (data as { vcs: Array<{ coordinates?: { latitude: number; longitude: number }; name: string; firm: string; location: string; links: string[]; match_score: number; explanation?: unknown }> }).vcs.forEach((vc) => {
        const { coordinates, name, firm, location, links, match_score } = vc;

        if (!coordinates?.latitude || !coordinates?.longitude) return;

        // Prepare VC data for sidebar
        const vcData = {
          type: 'vc',
          name,
          firm,
          location,
          match_score,
          links,
          coordinates,
          explanation: vc.explanation
        };

        // Create a custom VC marker element (different color to distinguish from audience)
        const el = document.createElement("div");
        el.className = "vc-marker";
        el.style.cssText = `
            background-color: #10b981;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          `;
        el.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" x2="12" y1="2" y2="22"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        `;

        const [lng, lat] = offsetDuplicateCoordinates(
          coordinates.latitude,
          coordinates.longitude,
          'vc'
        );

        const marker = new mapboxgl.Marker({ element: el, draggable: false })
          .setLngLat([lng, lat])
          .addTo(map);

        // Add click handler for sidebar
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          handlePinClick(vcData);
        });

        vcMarkersRef.current.push(marker);
      });
    } catch (error) {
      console.error("Error displaying VCs:", error);
    }
  }, [showVCs, vcsData, handlePinClick]);

  /** Handle Competitor toggle - display competitors as pins */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing competitor markers
    competitorMarkersRef.current.forEach((m) => m.remove());
    competitorMarkersRef.current = [];

    if (!showCompetitors || !competitorsData) return;

    // Use data from props
    const data = competitorsData;
    console.log("Displaying competitors on map:", data);

    try {
      // Add competitor markers to the map
      (data as { competitors: Array<{ coordinates?: { latitude: number; longitude: number }; company_name: string; location: string; links: string[]; date_founded: string; threat_score: number; explanation?: unknown }> }).competitors.forEach((competitor) => {
        const { coordinates, company_name, location, links, date_founded, threat_score } = competitor;

        if (!coordinates?.latitude || !coordinates?.longitude) return;

        // Prepare competitor data for sidebar
        const competitorData = {
          type: 'competitor',
          company_name,
          location,
          date_founded,
          threat_score,
          links,
          coordinates,
          explanation: competitor.explanation
        };

        // Create a custom competitor marker element (red color to distinguish)
        const el = document.createElement("div");
        el.className = "competitor-marker";
        el.style.cssText = `
            background-color: #ef4444;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          `;
        el.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5"></polyline>
            <line x1="13" x2="19" y1="19" y2="13"></line>
            <line x1="16" x2="20" y1="16" y2="20"></line>
            <line x1="19" x2="21" y1="21" y2="19"></line>
            <polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5"></polyline>
            <line x1="5" x2="9" y1="14" y2="18"></line>
            <line x1="7" x2="4" y1="17" y2="20"></line>
            <line x1="3" x2="5" y1="19" y2="21"></line>
          </svg>
        `;

        const [lng, lat] = offsetDuplicateCoordinates(
          coordinates.latitude,
          coordinates.longitude,
          'competitor'
        );

        const marker = new mapboxgl.Marker({ element: el, draggable: false })
          .setLngLat([lng, lat])
          .addTo(map);

        // Add click handler for sidebar
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          handlePinClick(competitorData);
        });

        competitorMarkersRef.current.push(marker);
      });
    } catch (error) {
      console.error("Error displaying competitors:", error);
    }
  }, [showCompetitors, competitorsData, handlePinClick]);

  /** Handle Cofounder toggle - display cofounders as pins */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing cofounder markers
    cofounderMarkersRef.current.forEach((m) => m.remove());
    cofounderMarkersRef.current = [];

    if (!showCofounders || !cofoundersData) return;

    // Use data from props
    const data = cofoundersData;
    console.log("Displaying cofounders on map:", data);

    try {

      // Add cofounder markers to the map
      (data as { cofounders: Array<{ coordinates?: { latitude: number; longitude: number }; name: string; location: string; links: string[]; match_score: number; explanation?: unknown }> }).cofounders.forEach((cofounder) => {
        const { coordinates, name, location, links, match_score } = cofounder;

        if (!coordinates?.latitude || !coordinates?.longitude) return;

        // Prepare cofounder data for sidebar
        const cofounderData = {
          type: 'cofounder',
          name,
          location,
          match_score,
          links,
          coordinates,
          explanation: cofounder.explanation
        };

        // Create a custom cofounder marker element (purple color to distinguish)
        const el = document.createElement("div");
        el.className = "cofounder-marker";
        el.style.cssText = `
            background-color: #8b5cf6;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          `;
        el.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        `;

        const [lng, lat] = offsetDuplicateCoordinates(
          coordinates.latitude,
          coordinates.longitude,
          'cofounder'
        );

        const marker = new mapboxgl.Marker({ element: el, draggable: false })
          .setLngLat([lng, lat])
          .addTo(map);

        // Add click handler for sidebar
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          handlePinClick(cofounderData);
        });

        cofounderMarkersRef.current.push(marker);
      });
    } catch (error) {
      console.error("Error displaying cofounders:", error);
    }
  }, [showCofounders, cofoundersData, handlePinClick]);

  /** Handle demographics data changes */
  useEffect(() => {
    if (demographicsData && mapRef.current) {
      console.log("Demographics data received, loading into map:", demographicsData);
      loadDemographicsData(demographicsData as AudienceCollection, showDemographics, marketAnalysisData, handlePinClick);
    }
  }, [demographicsData, showDemographics, marketAnalysisData, handlePinClick, loadDemographicsData]);

  /** Load FEMA shelter data */
  useEffect(() => {
    async function loadShelters() {
      const map = mapRef.current;
      if (!map) return;

      // Wait for map to be fully loaded
      if (!map.loaded()) {
        map.once('load', () => loadShelters());
        return;
      }

      try {
        console.log("Loading FEMA shelters...");
        const shelters = await getShelters(); // Get all shelters
        console.log("Loaded shelters:", shelters);

        // Clear existing shelter markers
        shelterMarkersRef.current.forEach(m => m.remove());
        shelterMarkersRef.current = [];

        // Create markers for each shelter
        shelters.forEach(shelter => {
          if (!shelter.latitude || !shelter.longitude) return;

          // Create blue marker element - LARGE for visibility
          const el = document.createElement("div");
          el.className = "shelter-marker";
          el.style.width = "40px";
          el.style.height = "40px";
          el.style.borderRadius = "50%";
          el.style.backgroundColor = "#00FFFF"; // Cyan/bright blue
          el.style.border = "4px solid #FF0000"; // RED border so we can't miss it
          el.style.boxShadow = "0 4px 16px rgba(0,255,255,0.8)";
          el.style.cursor = "pointer";
          el.style.zIndex = "1000";

          console.log("Creating marker for:", shelter.name, "at", [shelter.longitude, shelter.latitude]);

          const marker = new mapboxgl.Marker({ element: el })
            .setLngLat([shelter.longitude, shelter.latitude])
            .setPopup(
              new mapboxgl.Popup({ offset: 25 }).setHTML(
                `<div style="padding: 10px;">
                  <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">${shelter.name}</h3>
                  <p style="margin: 4px 0; font-size: 12px;"><strong>Address:</strong> ${shelter.address}, ${shelter.city}, ${shelter.state}</p>
                  <p style="margin: 4px 0; font-size: 12px;"><strong>Status:</strong> ${shelter.status}</p>
                  <p style="margin: 4px 0; font-size: 12px;"><strong>Organization:</strong> ${shelter.organization || "N/A"}</p>
                  <p style="margin: 4px 0; font-size: 12px;"><strong>Capacity:</strong> ${shelter.evacuation_capacity || "N/A"}</p>
                  <p style="margin: 4px 0; font-size: 12px;"><strong>Current Population:</strong> ${shelter.current_population || 0}</p>
                </div>`
              )
            )
            .addTo(mapRef.current!);

          shelterMarkersRef.current.push(marker);
        });

        console.log(`Added ${shelters.length} shelter markers to map`);
      } catch (error) {
        console.error("Failed to load shelters:", error);
      }
    }

    loadShelters();
  }, []);

  /** Handle demographics toggle - show heatmap when demographics is enabled */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (showDemographics && heatmapData) {
      // Clear any existing markers when demographics is enabled
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      // Remove existing heatmap first
      removeHeatmapLayer();

      // Add heatmap source
      map.addSource("audience-heatmap", {
        type: "geojson",
        data: heatmapData,
      });

      // Add heatmap layer
      addHeatmapLayer(marketAnalysisData, handlePinClick);
    } else {
      // When demographics is disabled, remove heatmap and clear all markers
      removeHeatmapLayer();
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    }
  }, [showDemographics, heatmapData, addHeatmapLayer, removeHeatmapLayer, marketAnalysisData, handlePinClick]);

  /** Change map style */
  const handleStyleChange = (newStyle: string) => {
    const map = mapRef.current;
    if (!map) return;

    setStyleUrl(newStyle);
    map.setStyle(newStyle); // 'style.load' handler will re-apply globe + optional 3D layer
    setShowStyleSelector(false);
  };

  /** Toggle styles using setStyle (no re-init) and preserve globe */
  const handleToggleTheme = () => {
    const map = mapRef.current;
    if (!map) return;

    const next = styleUrl === LIGHT_STYLE ? DARK_STYLE : LIGHT_STYLE;
    setStyleUrl(next);
    map.setStyle(next); // 'style.load' handler will re-apply globe + optional 3D layer
  };

  return (
    <div
      style={{
        position: "relative",
        height: "100vh",
        width: "100%",
        ...style,
      }}
      className={className}
    >
      {enableThemeToggle && (
        <div
          style={{
            position: "absolute",
            zIndex: 1,
            top: 10,
            left: 10,
            background: "white",
            borderRadius: 8,
            padding: "6px 10px",
            boxShadow: "0 4px 16px rgba(0,0,0,.12)",
          }}
        >
          <button onClick={handleToggleTheme}>
            {styleUrl === LIGHT_STYLE ? "Dark mode" : "Light (Globe)"}
          </button>
        </div>
      )}

      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

      {/* Map Style Selector */}
      <div className="fixed right-4 top-4 z-[9998] space-y-2">
        <button
          onClick={() => setShowStyleSelector(!showStyleSelector)}
          className="w-full rounded-lg bg-black/70 px-3 py-2 text-sm text-white backdrop-blur-md hover:bg-black/80"
        >
          🗺️ Map Style
        </button>
        
        {showStyleSelector && (
          <div className="w-48 space-y-1 rounded-lg bg-black/70 p-2 backdrop-blur-md">
            <button
              onClick={() => handleStyleChange(DARK_STYLE)}
              className={`w-full rounded px-3 py-2 text-left text-xs text-white transition ${
                styleUrl === DARK_STYLE ? "bg-blue-500" : "hover:bg-white/10"
              }`}
            >
              🌑 Dark
            </button>
            <button
              onClick={() => handleStyleChange(LIGHT_STYLE)}
              className={`w-full rounded px-3 py-2 text-left text-xs text-white transition ${
                styleUrl === LIGHT_STYLE ? "bg-blue-500" : "hover:bg-white/10"
              }`}
            >
              🌍 Globe (Light)
            </button>
            <button
              onClick={() => handleStyleChange(SATELLITE_STYLE)}
              className={`w-full rounded px-3 py-2 text-left text-xs text-white transition ${
                styleUrl === SATELLITE_STYLE ? "bg-blue-500" : "hover:bg-white/10"
              }`}
            >
              🛰️ Satellite + Streets
            </button>
            <button
              onClick={() => handleStyleChange(SATELLITE_PURE)}
              className={`w-full rounded px-3 py-2 text-left text-xs text-white transition ${
                styleUrl === SATELLITE_PURE ? "bg-blue-500" : "hover:bg-white/10"
              }`}
            >
              📡 Satellite Only
            </button>
          </div>
        )}
      </div>

      {/* Sensitivity Controls */}
      {enableHandTracking && (
        <div className="fixed right-4 top-20 z-[9998]">
          <button
            onClick={() => setShowSensitivityControls(!showSensitivityControls)}
            className="rounded-lg bg-black/70 px-3 py-2 text-sm text-white backdrop-blur-md hover:bg-black/80"
          >
            ⚙️ Gesture Settings
          </button>
          
          {showSensitivityControls && (
            <div className="mt-2 w-64 space-y-4 rounded-lg bg-black/70 p-4 backdrop-blur-md">
              <h3 className="text-sm font-semibold text-white">Sensitivity Controls</h3>
              
              <Slider
                value={rotationSensitivity}
                onChange={setRotationSensitivity}
                min={0.1}
                max={5}
                step={0.1}
                label="Rotation Sensitivity"
              />
              
              <Slider
                value={zoomSensitivity}
                onChange={setZoomSensitivity}
                min={0.005}
                max={0.2}
                step={0.005}
                label="Zoom Sensitivity"
              />
              
              <button
                onClick={() => {
                  setRotationSensitivity(0.5);
                  setZoomSensitivity(0.05);
                }}
                className="w-full rounded bg-blue-500 px-3 py-1.5 text-xs text-white hover:bg-blue-600"
              >
                Reset to Defaults
              </button>
            </div>
          )}
        </div>
      )}

      {/* Hand Tracking Overlay */}
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

      {/* Unified Pin Sidebar */}
      <UnifiedPinSidebar
        pinData={selectedPinData as never}
        isVisible={sidebarVisible}
        onClose={handleSidebarClose}
        position="left"
        width="400px"
      />
    </div>
  );
}
