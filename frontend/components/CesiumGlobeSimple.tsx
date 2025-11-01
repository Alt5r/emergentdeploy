"use client";

import React, { useEffect, useRef, useState } from "react";
import { getShelters, type Shelter } from "@/lib/shelters-api";

// Set Cesium base URL BEFORE any imports
if (typeof window !== 'undefined') {
  (window as any).CESIUM_BASE_URL = '/cesium';
}

export default function CesiumGlobeSimple({ className }: { className?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [storms, setStorms] = useState<any[]>([]);
  const [tsunamiStations, setTsunamiStations] = useState<any[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [cssLoaded, setCssLoaded] = useState(false);

  // Load Cesium CSS
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/cesium/Widgets/widgets.css';
    link.onload = () => setCssLoaded(true);
    document.head.appendChild(link);

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  // Fetch all data
  useEffect(() => {
    async function loadAllData() {
      try {
        // Load shelters
        const shelterData = await getShelters();
        console.log("Shelters loaded:", shelterData);
        setShelters(shelterData);

        // Load tropical storms
        const stormResponse = await fetch('http://localhost:8000/api/v1/storms');
        const stormData = await stormResponse.json();
        console.log("Storms API response:", stormData);
        // Handle nested structure: stormData.storms.storms
        const stormsArray = stormData.storms?.storms || stormData.storms || [];
        console.log("Parsed storms:", stormsArray);
        setStorms(stormsArray);

        // Load tsunami stations
        const tsunamiResponse = await fetch('http://localhost:8000/api/v1/tsunami/stations');
        const tsunamiData = await tsunamiResponse.json();
        console.log("Tsunami stations loaded:", tsunamiData);
        setTsunamiStations(tsunamiData.stations || []);

      } catch (error) {
        console.error("Failed to load data:", error);
      }
    }
    loadAllData();
  }, []);

  // Initialize Cesium
  useEffect(() => {
    if (!containerRef.current || typeof window === 'undefined' || !cssLoaded) return;

    // Dynamically import Cesium
    import('cesium').then(async (Cesium) => {
      console.log("Cesium module loaded");

      // Set base URL for assets
      (window as any).CESIUM_BASE_URL = '/cesium';
      console.log("CESIUM_BASE_URL set to:", '/cesium');

      // Set Cesium Ion access token
      Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJmYzhjNzJiZi0xMWYzLTQxYzctOWNkNC0yNzhhMzg0Njg3ZDAiLCJpZCI6MzU2MTExLCJpYXQiOjE3NjIwMTI4MDV9.lp1RrpCUxvSRG-VdbsVEjSLlccbFGFOm5OeE_qi6z70';
      console.log("Cesium Ion token set");

      // Create viewer with Cesium Ion imagery and 3D terrain
      console.log("Creating Cesium Viewer with Ion imagery and terrain...");
      const viewer = new Cesium.Viewer(containerRef.current!, {
        timeline: false,
        animation: false,
        baseLayerPicker: true, // Enable to see different map styles
        geocoder: false,
        homeButton: true,
        sceneModePicker: true, // Allow 2D/3D/Columbus view
        navigationHelpButton: false,
        fullscreenButton: true,
        infoBox: true,
        selectionIndicator: true,
        terrainProvider: await Cesium.createWorldTerrainAsync({
          requestWaterMask: true, // Show water bodies
          requestVertexNormals: true, // Better lighting
        }),
      });
      console.log("Viewer created with Ion imagery and 3D terrain");

      // Log globe state
      console.log("Globe:", viewer.scene.globe);
      console.log("Imagery layers count:", viewer.imageryLayers.length);
      console.log("Base layer:", viewer.imageryLayers.get(0));

      // Remove Cesium Ion credit
      viewer.cesiumWidget.creditContainer.style.display = 'none';
      console.log("Credit hidden");

      viewerRef.current = viewer;

      // Position camera to show North America
      console.log("Positioning camera...");
      viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(-95.0, 40.0, 15000000),
      });
      console.log("Camera positioned");

      // Make sure the globe fills the container
      viewer.resize();
      console.log("Viewer resized");

      setIsLoaded(true);

      console.log("✅ Cesium viewer fully initialized");
    }).catch(error => {
      console.error("Failed to load Cesium:", error);
    });

    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy();
      }
    };
  }, [cssLoaded]);

  // Add shelter entities when loaded
  useEffect(() => {
    if (!isLoaded || !viewerRef.current || shelters.length === 0) return;

    import('cesium').then((Cesium) => {
      const viewer = viewerRef.current;

      console.log("Adding shelter entities:", shelters);

      shelters.forEach(shelter => {
        viewer.entities.add({
          name: shelter.name,
          position: Cesium.Cartesian3.fromDegrees(shelter.longitude, shelter.latitude),
          point: {
            pixelSize: 12,
            color: Cesium.Color.fromCssColorString('#1e3a8a'), // Dark blue
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.5, 1.5e7, 0.5),
          },
          description: `
            <div style="padding: 14px;">
              <h3 style="color: #3b82f6; margin: 0 0 10px 0; font-weight: 600;">${shelter.name}</h3>
              <p style="margin: 6px 0; color: #e5e7eb;">📍 ${shelter.city}, ${shelter.state}</p>
              <p style="margin: 6px 0; color: #10b981;">🟢 ${shelter.status}</p>
              <p style="margin: 6px 0; color: #e5e7eb;">📊 Population: ${shelter.current_population || 0}</p>
              ${shelter.capacity ? `<p style="margin: 6px 0; color: #e5e7eb;">👥 Capacity: ${shelter.capacity}</p>` : ''}
            </div>
          `,
        });
      });

      console.log(`Added ${shelters.length} shelter entities`);

      // Add tropical storm/hurricane entities
      if (storms.length > 0) {
        console.log("Adding storm entities:", storms);

        storms.forEach(storm => {
          // Parse coordinates - handle nested current_position
          const latStr = storm.current_position?.latitude || storm.latitude || '0';
          const lonStr = storm.current_position?.longitude || storm.longitude || '0';

          const lat = parseFloat(latStr.toString().replace('N', '').replace('S', '-'));
          const lon = -Math.abs(parseFloat(lonStr.toString().replace('W', '').replace('E', '-'))); // West is negative

          console.log(`Storm ${storm.name} position:`, lat, lon);

          // Color based on category
          const getStormColor = (severity: string) => {
            if (severity.includes('Category 5') || severity.includes('Category 4')) {
              return Cesium.Color.RED;
            } else if (severity.includes('Category 3')) {
              return Cesium.Color.ORANGE;
            } else if (severity.includes('Category 2') || severity.includes('Category 1')) {
              return Cesium.Color.YELLOW;
            }
            return Cesium.Color.CYAN;
          };

          const stormColor = getStormColor(storm.severity || '');

          // Add hurricane marker with pulsing ring
          viewer.entities.add({
            name: `🌀 ${storm.name}`,
            position: Cesium.Cartesian3.fromDegrees(lon, lat, 5000),
            point: {
              pixelSize: 20,
              color: stormColor,
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 3,
            },
            ellipse: {
              semiMinorAxis: 100000, // 100km radius
              semiMajorAxis: 100000,
              material: stormColor.withAlpha(0.2),
              outline: true,
              outlineColor: stormColor.withAlpha(0.6),
              outlineWidth: 2,
            },
            description: `
              <div style="padding: 16px;">
                <h3 style="color: #ef4444; margin: 0 0 10px 0; font-weight: 700;">🌀 ${storm.classification} ${storm.name}</h3>
                <p style="margin: 6px 0; color: #fca5a5; font-weight: 600;">${storm.severity}</p>
                <p style="margin: 8px 0; color: #e5e7eb;">📍 Position: ${latStr}, ${lonStr}</p>
                <p style="margin: 6px 0; color: #e5e7eb;">💨 Winds: ${storm.intensity?.max_sustained_winds_knots || storm.wind_speed_kt} knots</p>
                <p style="margin: 6px 0; color: #e5e7eb;">🌪️ Pressure: ${storm.intensity?.pressure_mb || storm.pressure} mb</p>
                <p style="margin: 6px 0; color: #e5e7eb;">➡️ Movement: ${storm.movement}</p>
              </div>
            `,
          });
        });

        console.log(`Added ${storms.length} storm entities`);
      }

      // Add tsunami buoy stations
      if (tsunamiStations.length > 0) {
        console.log("Adding tsunami station entities:", tsunamiStations.length);

        tsunamiStations.forEach(station => {
          viewer.entities.add({
            name: `🌊 DART ${station.station_id}`,
            position: Cesium.Cartesian3.fromDegrees(station.longitude, station.latitude),
            point: {
              pixelSize: 8,
              color: Cesium.Color.fromCssColorString('#06b6d4'), // Cyan for tsunami
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 1,
            },
            description: `
              <div style="padding: 12px;">
                <h3 style="color: #06b6d4; margin: 0 0 8px 0; font-weight: 600;">🌊 DART Station ${station.station_id}</h3>
                <p style="margin: 4px 0; color: #e5e7eb;">📍 Tsunami Monitoring Buoy</p>
                <p style="margin: 4px 0; color: #e5e7eb;">Lat: ${station.latitude.toFixed(3)}</p>
                <p style="margin: 4px 0; color: #e5e7eb;">Lon: ${station.longitude.toFixed(3)}</p>
              </div>
            `,
          });
        });

        console.log(`Added ${tsunamiStations.length} tsunami station entities`);
      }
    });
  }, [isLoaded, shelters, storms, tsunamiStations]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        margin: 0,
        padding: 0,
      }}
    />
  );
}
