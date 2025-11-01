"use client";

import { useState } from "react";
import AppPage from "./appPage";
import { StartupProvider, useStartup } from "@/contexts/StartupContext";
import { useBackgroundAPI } from "@/hooks/useBackgroundAPI";

function AppContent() {
  const { startupIdea, setStartupIdea } = useStartup();
  
  // Start background API calls when startup idea is available
  useBackgroundAPI(startupIdea);

  const [initialQuery, setInitialQuery] = useState("");
  const [isGeneratingPitchDeck, setIsGeneratingPitchDeck] = useState(false);

  const handleGeneratePitchDeck = async () => {
    setIsGeneratingPitchDeck(true);

    try {
      const response = await fetch("http://localhost:8000/generate-pitch-deck", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          idea: initialQuery || startupIdea || "AI for legal technology",
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate pitch deck: ${response.status}`);
      }

      const data = await response.json();
      console.log("Pitch deck generated:", data);

      // Download the PowerPoint file if available
      if (data.pptx_file) {
        const downloadUrl = `http://localhost:8000/download-pitch-deck/${data.pptx_file}`;

        // Create a temporary anchor element to trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = data.pptx_file;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error("Error generating pitch deck:", error);
    } finally {
      setIsGeneratingPitchDeck(false);
    }
  };

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <AppPage 
        initialQuery={initialQuery || startupIdea}
        onGeneratePitchDeck={handleGeneratePitchDeck}
        isGeneratingPitchDeck={isGeneratingPitchDeck}
      />
    </div>
  );
}

export default function Home() {
  return (
    <StartupProvider>
      <AppContent />
    </StartupProvider>
  );
}


