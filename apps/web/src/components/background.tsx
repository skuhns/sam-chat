"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { getLocation, type LocationKey } from "@sam-chat/locations";
import { applyLayerPolicy, applyLayoutOverrides, applyPaintOverrides } from "lib/map-layers";

const DEFAULT_STYLE_URL = `/mapstyles/topo-v2.json`;

export default function BackgroundMap({
  location = "chicago",
  interactive = false,
  darken = 0.4,
  blurPx = 0,
}: {
  location?: LocationKey;
  interactive?: boolean;
  darken?: number;
  blurPx?: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const styleUrlRef = useRef<string | null>(null);


  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const loc = getLocation(location);
    const styleUrl = DEFAULT_STYLE_URL;
    styleUrlRef.current = DEFAULT_STYLE_URL;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [loc.camera.lng, loc.camera.lat],
      zoom: loc.camera.zoom ?? 11,
      bearing: loc.camera.bearing ?? 0,
      pitch: loc.camera.pitch ?? 0,
      attributionControl: false,
      interactive,
    });

    if (!interactive) {
      map.scrollZoom.disable();
      map.boxZoom.disable();
      map.dragPan.disable();
      map.dragRotate.disable();
      map.keyboard.disable();
      map.doubleClickZoom.disable();
      map.touchZoomRotate.disable();
    }

    map.on("style.load", () => {
      applyLayerPolicy(map, loc.layers);
      applyPaintOverrides(map, loc.paintOverrides);
      applyLayoutOverrides(map, loc.layoutOverrides);
      setMapReady(true);
    });

    if (process.env.NODE_ENV === "development") {
      (window as any).__bgmap = map;
    }

    mapRef.current = map;
    return () => map.remove();
  }, []);

  //Respond to location changes safely
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const loc = getLocation(location);
    const nextStyleUrl = DEFAULT_STYLE_URL;

    const applyAll = () => {
      applyLayerPolicy(map, loc.layers);
      applyPaintOverrides(map, loc.paintOverrides);
      applyLayoutOverrides(map, loc.layoutOverrides);

      map.easeTo({
        center: [loc.camera.lng, loc.camera.lat],
        zoom: loc.camera.zoom ?? map.getZoom(),
        bearing: loc.camera.bearing ?? map.getBearing(),
        pitch: loc.camera.pitch ?? map.getPitch(),
        duration: 1100,
      });
    };

    if (styleUrlRef.current !== nextStyleUrl) {
      styleUrlRef.current = nextStyleUrl;
      setMapReady(false);
      map.setStyle(nextStyleUrl);
      map.once("style.load", () => {
        setMapReady(true);
        applyAll();
      });
      return;
    }

    if (!mapReady) {
      map.once("style.load", applyAll);
      return;
    }

    applyAll();
  }, [location, mapReady]);

  return (
    <div
      aria-hidden
      className="fixed inset-0 "
      style={{ filter: blurPx ? `blur(${blurPx}px)` : undefined }}
    >
      <div id="bgmap" ref={containerRef} className="h-full w-full" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            `linear-gradient(0deg, rgba(0,0,0,${darken}), rgba(0,0,0,${darken})),` +
            `radial-gradient(1200px 800px at 50% -20%, rgba(0,0,0,0.25), transparent 70%)`,
        }}
      />
    </div>
  );
}
