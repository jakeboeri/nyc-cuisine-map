/**
 * Configuration for NYC Cuisine Pointillism Map
 */

// Convert RGB array to CSS hex string
export function rgbToHex(rgb) {
  if (!rgb || rgb.length < 3) return '#888888';
  return '#' + rgb.map(c => c.toString(16).padStart(2, '0')).join('');
}

// Initial view state centered on NYC
export const INITIAL_VIEW_STATE = {
  longitude: -73.98,
  latitude: 40.75,
  zoom: 11,
  pitch: 0,
  bearing: 0,
  minZoom: 9,
  maxZoom: 18,
};

// Map style URL (CartoDB Dark Matter - dark neon aesthetic)
export const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

// Point styling
export const POINT_RADIUS = 25; // meters
export const POINT_RADIUS_MIN_PIXELS = 2;
export const POINT_RADIUS_MAX_PIXELS = 10;
export const POINT_OPACITY = 0.9;

// HeatmapLayer settings
export const HEATMAP_RADIUS_PIXELS = 50; // pixel radius of influence
export const HEATMAP_INTENSITY = 2; // intensity multiplier
export const HEATMAP_THRESHOLD = 0.03; // minimum alpha threshold
export const HEATMAP_OPACITY = 0.6; // layer opacity
