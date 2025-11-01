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

  // Fetch shelter data
  useEffect(() => {
    async function loadShelters() {
      try {
        const data = await getShelters();
        console.log("Shelters loaded for Cesium:", data);
        setShelters(data);
      } catch (error) {
        console.error("Failed to load shelters:", error);
      }
    }
    loadShelters();
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
    });
  }, [isLoaded, shelters]);

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
