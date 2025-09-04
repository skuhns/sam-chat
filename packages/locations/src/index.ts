// packages/locations/src/index.ts

/** Canonical ID for each location. Extend as you add more. */
export type LocationKey =
  | "chicago"
  | "tetons"
  | "purdue"
  | "chiang_mai"
  | "wind_river_range"
  | "bangkok"
  | "paris"
  | "berlin"
  | "mexico_city"
  | "guadalajara"
  | "nyc"
  | "san_francisco"
  | "yosemite"
  | "rocky_mountains"
  | "grandfather_mountain"
  | "siem_reap"
  | "sanibel_island"
  | "indianapolis";

// /** Minimal map camera definition */
export interface Camera {
  lng: number;
  lat: number;
  zoom?: number;
  bearing?: number;
  pitch?: number;
}

/** A matcher can be a literal id, a regex, or a function */
export type LayerMatcher = string | RegExp | ((layerId: string) => boolean);

/** Composable policy: mix allow, deny, and a predicate. */
export interface LayerPolicy {
  /**
   * If any matcher here matches, the layer is forced visible.
   * Highest precedence (wins over deny).
   */
  allow?: LayerMatcher[];

  /**
   * If any matcher here matches (and not allowed), the layer is hidden.
   */
  deny?: LayerMatcher[];

  /**
   * Predicate applied if not matched by allow/deny.
   * Return true to show, false to hide.
   */
  test?: (layerId: string) => boolean;

  /**
   * What to do if nothing matched and no test is provided.
   * - true  => force show
   * - false => force hide
   * - "style" => leave the style’s current visibility untouched
   */
  defaultVisibility?: boolean | "style";
}
/** Optional paint tweaks per layer (thin wrapper to avoid importing maplibre types here) */
export type PaintOverrides = Record<
  string, // layerId
  Record<string, unknown> // paint properties
>;

/** Optional layout tweaks per layer */
export type LayoutOverrides = Record<
  string, // layerId
  Record<string, unknown> // layout properties
>;

/** A complete location definition */
export interface LocationConfig {
  key: LocationKey;
  label: string;
  /** Default camera for background */
  camera: Camera;

  /**
   * Which layers should be visible for this location.
   * If omitted, we'll default to "contours only" (see DEFAULT_CONTOURS_POLICY below).
   */
  layers?: LayerPolicy;
  /** Optional paint/layout overrides per location */
  paintOverrides?: PaintOverrides;
  layoutOverrides?: LayoutOverrides;
}

/** Default: (keeps background quiet/nice) */

export const DEFAULT_POLICY: LayerPolicy = {
  deny: ["Contour labels", "Glacier contour labels"],
  allow: ["Lake labels", "Water", "Major road", "Forest"],
  test: (id) => id.toLowerCase().includes("contour"),
  defaultVisibility: false,
};

export const DEFAULT_PAINT: PaintOverrides = {
  Water: {
    "fill-color": "#5c5a57",
    "fill-opacity": 0.2,
  },
  Forest: {
    "fill-color": "#5c5a57",
    "fill-opacity": 1,
  },
  "Major road": {
    "line-color": "#5c5a57",
    "line-opacity": 0.4,
    "line-width": 0.775,
  },
};

function matches(id: string, m: LayerMatcher): boolean {
  if (typeof m === "string") return id === m;
  if (m instanceof RegExp) return m.test(id);
  return m(id);
}

/**
 * Decide visibility given a policy.
 * Returns: "visible", "none", or "unchanged" (when defaultVisibility === "style").
 */
export function decideLayerVisibility(
  layerId: string,
  policy?: LayerPolicy
): "visible" | "none" | "unchanged" {
  if (!policy) return "unchanged";

  const { allow, deny, test, defaultVisibility = "style" } = policy;

  // 1) allow wins
  if (allow?.some((m) => matches(layerId, m))) return "visible";

  // 2) deny next
  if (deny?.some((m) => matches(layerId, m))) return "none";

  // 3) predicate
  if (typeof test === "function") return test(layerId) ? "visible" : "none";

  // 4) fallback
  if (defaultVisibility === "style") return "unchanged";
  return defaultVisibility ? "visible" : "none";
}
/** Library of known locations. Add as many as you want. */
export const LOCATIONS: Record<LocationKey, LocationConfig> = {
  chicago: {
    key: "chicago",
    label: "Chicago, IL",
    camera: { lat: 41.8788, lng: -87.6398, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  tetons: {
    key: "tetons",
    label: "Teton Range",
    camera: { lat: 43.7904, lng: -110.8918, zoom: 10.3 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  purdue: {
    key: "purdue",
    label: "Purdue University",
    camera: { lat: 40.4237, lng: -86.9212, zoom: 13 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  chiang_mai: {
    key: "chiang_mai",
    label: "Chiang Mai, Thailand",
    camera: { lat: 18.7883, lng: 98.9853, zoom: 12 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  wind_river_range: {
    key: "wind_river_range",
    label: "Wind River Range, WY",
    camera: { lat: 43.1667, lng: -109.65, zoom: 9 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  bangkok: {
    key: "bangkok",
    label: "Bangkok, Thailand",
    camera: { lat: 13.7563, lng: 100.5018, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  paris: {
    key: "paris",
    label: "Paris, France",
    camera: { lat: 48.8566, lng: 2.3522, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  berlin: {
    key: "berlin",
    label: "Berlin, Germany",
    camera: { lat: 52.52, lng: 13.405, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  mexico_city: {
    key: "mexico_city",
    label: "Mexico City, Mexico",
    camera: { lat: 19.4326, lng: -99.1332, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  guadalajara: {
    key: "guadalajara",
    label: "Guadalajara, Mexico",
    camera: { lat: 20.6597, lng: -103.3496, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },
  nyc: {
    key: "nyc",
    label: "New York City, NY",
    camera: { lat: 40.7128, lng: -74.006, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  san_francisco: {
    key: "san_francisco",
    label: "San Francisco, CA",
    camera: { lat: 37.7749, lng: -122.4194, zoom: 11.2 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  yosemite: {
    key: "yosemite",
    label: "Yosemite National Park, CA",
    camera: { lat: 37.8651, lng: -119.5383, zoom: 10 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  rocky_mountains: {
    key: "rocky_mountains",
    label: "Rocky Mountains, CO",
    camera: { lat: 40.3428, lng: -105.6836, zoom: 9.5 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  grandfather_mountain: {
    key: "grandfather_mountain",
    label: "Grandfather Mountain, NC",
    camera: { lat: 36.1, lng: -81.8117, zoom: 12 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  siem_reap: {
    key: "siem_reap",
    label: "Siem Reap, Cambodia",
    camera: { lat: 13.3671, lng: 103.8448, zoom: 12 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  sanibel_island: {
    key: "sanibel_island",
    label: "Sanibel Island, FL",
    camera: { lat: 26.4489, lng: -82.0223, zoom: 12 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },

  indianapolis: {
    key: "indianapolis",
    label: "Indianapolis, IN",
    camera: { lat: 39.7684, lng: -86.1581, zoom: 11 },
    layers: DEFAULT_POLICY,
    paintOverrides: DEFAULT_PAINT,
  },
};

/** Convenience accessor */
export function getLocation(key: LocationKey): LocationConfig {
  return LOCATIONS[key];
}
