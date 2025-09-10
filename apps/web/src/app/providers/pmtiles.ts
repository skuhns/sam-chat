"use client";

import { useEffect } from "react";
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";

export default function PMTilesProvider() {
  useEffect(() => {
    const proto = new Protocol();
    (maplibregl as any).addProtocol("pmtiles", proto.tile);
    return () => {
      (maplibregl as any).removeProtocol?.("pmtiles");
    };
  }, []);
  return null;
}
