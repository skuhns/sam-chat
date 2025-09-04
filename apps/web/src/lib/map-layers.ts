// src/app/lib/mapLayers.ts
import type { Map } from "maplibre-gl";
import { type PaintOverrides, type LayoutOverrides, type LayerPolicy, decideLayerVisibility } from "@sam-chat/locations";

/**
 * Show/hide base layers according to the policy.
 * Call this after style.load.
 */
export function applyLayerPolicy(map: Map, policy?: LayerPolicy) {
  const layers = map.getStyle().layers ?? [];
  for (const layer of layers) {
    const decision = decideLayerVisibility(layer.id, policy);
    if (decision === "unchanged") continue;
    map.setLayoutProperty(layer.id, "visibility", decision === "visible" ? "visible" : "none");
  }
}

/** Apply optional paint overrides (safe no-throw version) */
export function applyPaintOverrides(map: Map, overrides?: PaintOverrides) {
  if (!overrides) return;
  for (const [layerId, paint] of Object.entries(overrides)) {
    for (const [prop, val] of Object.entries(paint)) {
      try {
        map.setPaintProperty(layerId, prop, val as any);
      } catch {
        // layer may not exist in given style — ignore
      }
    }
  }
}

/** Apply optional layout overrides */
export function applyLayoutOverrides(map: Map, overrides?: LayoutOverrides) {
  if (!overrides) return;
  for (const [layerId, layout] of Object.entries(overrides)) {
    for (const [prop, val] of Object.entries(layout)) {
      try {
        map.setLayoutProperty(layerId, prop, val as any);
      } catch {
        // ignore if layer missing
      }
    }
  }
}
