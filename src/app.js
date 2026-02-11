/**
 * NYC Cuisine Pointillism Map
 * Interactive visualization of NYC restaurants by cuisine category
 * Features collapsible legend grouped by geographic region
 */

import { Deck } from '@deck.gl/core';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import maplibregl from 'maplibre-gl';
import {
  rgbToHex,
  INITIAL_VIEW_STATE,
  MAP_STYLE,
  POINT_RADIUS,
  POINT_RADIUS_MIN_PIXELS,
  POINT_RADIUS_MAX_PIXELS,
  HEATMAP_RADIUS_PIXELS,
  HEATMAP_INTENSITY,
  HEATMAP_THRESHOLD,
  HEATMAP_OPACITY,
} from './config.js';

// State
let allData = [];
let filteredData = [];
let visibleCategories = new Set();  // Set of specific categories (leaf nodes)
let expandedGroups = new Set();     // Set of expanded category names
let hierarchy = {};                  // Nested {name: {count, color, children?: {...}}}
let categoryColors = {};            // {category: [r, g, b]}
let deck = null;
let map = null;

// View mode state
let showPoints = true;              // Toggle for points view (default)
let showHeatmap = false;            // Toggle for heatmap glow layer
let savedCategories = new Set();    // Saved selections when entering glow mode
let glowCategory = null;            // Currently selected category in glow mode

// Animation state
let legendHoverCategory = null;     // category hovered in legend (Points mode only)
let pulseStartTime = null;          // timestamp when pulse animation began
let pulseFrameId = null;            // requestAnimationFrame ID for pulse

// Hover descendants cache
let _hoverDescendantsCache = null;
let _hoverDescendantsCacheKey = null;

// DOM elements
const loadingEl = document.getElementById('loading');
const legendItemsEl = document.getElementById('legend-items');
const restaurantCountEl = document.getElementById('restaurant-count');
const tooltipEl = document.getElementById('tooltip');
const selectAllBtn = document.getElementById('select-all');
const selectNoneBtn = document.getElementById('select-none');
const togglePointsBtn = document.getElementById('toggle-points');
const toggleGlowBtn = document.getElementById('toggle-glow');

/**
 * Initialize the application
 */
async function init() {
  try {
    // Load restaurant data
    const data = await loadData();
    allData = data.restaurants;
    hierarchy = data.hierarchy;
    categoryColors = data.colors;

    // Initialize all categories as visible by collecting unique categories from data
    for (const restaurant of allData) {
      if (restaurant.category) {
        visibleCategories.add(restaurant.category);
      }
    }
    // Also add hierarchy grouping nodes so parent checkboxes show as fully checked
    function addGroupNodes(nodes) {
      for (const name in nodes) {
        visibleCategories.add(name);
        if (nodes[name].children) {
          addGroupNodes(nodes[name].children);
        }
      }
    }
    addGroupNodes(hierarchy);

    // Set up legend
    setupLegend();

    // Initialize map and deck
    initMap();

    // Hide loading overlay
    loadingEl.classList.add('hidden');

    // Initial render
    updateFilteredData();
    renderDeck();
  } catch (error) {
    console.error('Failed to initialize:', error);
    loadingEl.innerHTML = `
      <div class="loading-content">
        <p style="color: #c00;">Error loading data. Please run the preprocessing scripts first:</p>
        <code style="display: block; margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
          python scripts/prepare_map_data.py
        </code>
      </div>
    `;
  }
}

/**
 * Load preprocessed restaurant data
 */
async function loadData() {
  const response = await fetch('./map_data.json');
  if (!response.ok) {
    throw new Error('Data file not found. Run prepare_map_data.py first.');
  }
  return response.json();
}

/**
 * Initialize MapLibre GL basemap
 */
function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: MAP_STYLE,
    center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
    zoom: INITIAL_VIEW_STATE.zoom,
    pitch: INITIAL_VIEW_STATE.pitch,
    bearing: INITIAL_VIEW_STATE.bearing,
    interactive: false, // Deck.gl will handle interactions
    attributionControl: false, // We'll add our own in bottom-left
  });

  // Add attribution control to bottom-left with custom data source info
  const attrib = new maplibregl.AttributionControl({
    compact: true,
    customAttribution: 'Data: DOHMH New York City Restaurant Inspection Results (Jan 2026) &amp; Google Maps (Jan 2026). Categorization based on DOHMH and Google Maps tags and may contain errors.',
  });
  map.addControl(attrib, 'bottom-left');

  // Force attribution to start collapsed (MapLibre auto-expands on desktop)
  map.on('load', () => {
    const attribEl = document.querySelector('.maplibregl-ctrl-attrib');
    if (attribEl) {
      attribEl.classList.remove('maplibregl-compact-show');
    }
  });

  // Initialize Deck.gl
  deck = new Deck({
    canvas: 'deck-canvas',
    initialViewState: INITIAL_VIEW_STATE,
    controller: true,
    onViewStateChange: ({ viewState }) => {
      // Sync MapLibre with Deck.gl view
      map.jumpTo({
        center: [viewState.longitude, viewState.latitude],
        zoom: viewState.zoom,
        bearing: viewState.bearing,
        pitch: viewState.pitch,
      });
    },
    onHover: handleHover,
    layers: [], // Will be set by renderDeck()
  });
}

/**
 * Update filtered data based on visible categories
 */
function updateFilteredData() {
  filteredData = allData.filter(d => visibleCategories.has(d.category));
  updateRestaurantCount();
}

/**
 * Start the pulse animation loop for legend hover
 */
function startPulseLoop() {
  if (pulseFrameId) return;
  function pulse() {
    renderDeck();
    if (legendHoverCategory) {
      pulseFrameId = requestAnimationFrame(pulse);
    }
  }
  pulseFrameId = requestAnimationFrame(pulse);
}

/**
 * Stop the pulse animation loop
 */
function stopPulseLoop() {
  if (pulseFrameId) {
    cancelAnimationFrame(pulseFrameId);
    pulseFrameId = null;
  }
}

/**
 * Get cached set of descendant categories for the hovered legend item
 */
function getHoverDescendants() {
  if (_hoverDescendantsCacheKey === legendHoverCategory) return _hoverDescendantsCache;
  const nodeData = findNodeInHierarchy(legendHoverCategory);
  const list = nodeData ? getAllDescendantCategories(nodeData, legendHoverCategory) : [legendHoverCategory];
  _hoverDescendantsCache = new Set(list);
  _hoverDescendantsCacheKey = legendHoverCategory;
  return _hoverDescendantsCache;
}

/**
 * Render/update all Deck.gl layers based on current state
 */
function renderDeck() {
  if (!deck) return;

  try {
    const layers = [];

    if (showHeatmap && glowCategory) {
      // Glow mode: heatmap for the single selected category
      const nodeData = findNodeInHierarchy(glowCategory);
      const descendants = nodeData ? getAllDescendantCategories(nodeData, glowCategory) : [glowCategory];
      const heatmapData = allData.filter(d => descendants.includes(d.category));
      const color = (nodeData && nodeData.color) || categoryColors[glowCategory] || [255, 165, 0];

      // Scale intensity relative to total data so small categories don't look as bright as large ones
      const ratio = heatmapData.length / allData.length;
      const scaledIntensity = HEATMAP_INTENSITY * Math.sqrt(ratio) * 3;

      layers.push(createHeatmapLayer(heatmapData, color, glowCategory, scaledIntensity));
    } else if (showPoints) {
      // Points mode: show scatterplot
      layers.push(createScatterplotLayer());
    }

    deck.setProps({ layers });
  } catch (error) {
    console.error('Error rendering layers:', error);
  }
}

/**
 * Create the ScatterplotLayer with entrance + hover animations
 */
function createScatterplotLayer() {
  const now = performance.now();

  return new ScatterplotLayer({
    id: 'restaurants-scatter',
    data: filteredData,
    getPosition: d => d.position,
    getFillColor: d => {
      const base = categoryColors[d.category] || [128, 128, 128];

      if (legendHoverCategory) {
        const descendants = getHoverDescendants();
        if (descendants.has(d.category)) {
          return [base[0], base[1], base[2], 255]; // full brightness
        }
        return [base[0], base[1], base[2], 13]; // 5% — nearly invisible
      }

      return [base[0], base[1], base[2], 230];
    },
    getRadius: d => {
      if (legendHoverCategory && pulseStartTime) {
        const descendants = getHoverDescendants();
        if (descendants.has(d.category)) {
          const pulseElapsed = now - pulseStartTime;
          const pulse = (Math.sin(pulseElapsed * 0.005) + 1) / 2; // 0-1 at ~0.8Hz
          return POINT_RADIUS * (1.4 + pulse * 2.1); // 140-350% size
        }
      }

      return POINT_RADIUS;
    },
    radiusMinPixels: POINT_RADIUS_MIN_PIXELS,
    radiusMaxPixels: POINT_RADIUS_MAX_PIXELS,
    pickable: true,
    updateTriggers: {
      getFillColor: [legendHoverCategory, now],
      getRadius: [legendHoverCategory, now],
    },
  });
}

/**
 * Create a HeatmapLayer for a single cuisine category
 */
function createHeatmapLayer(data, color, cuisineId, intensity) {
  const baseColor = color || [255, 165, 0];
  const safeId = cuisineId.replace(/[^a-zA-Z0-9]/g, '_');

  return new HeatmapLayer({
    id: `heatmap-${safeId}`,
    data: data,
    getPosition: d => d.position,
    getWeight: 1,
    radiusPixels: HEATMAP_RADIUS_PIXELS,
    intensity: intensity || HEATMAP_INTENSITY,
    threshold: HEATMAP_THRESHOLD,
    opacity: HEATMAP_OPACITY,
    colorRange: [
      [baseColor[0], baseColor[1], baseColor[2], 0],
      [baseColor[0], baseColor[1], baseColor[2], 25],
      [baseColor[0], baseColor[1], baseColor[2], 85],
      [baseColor[0], baseColor[1], baseColor[2], 127],
      [baseColor[0], baseColor[1], baseColor[2], 180],
      [baseColor[0], baseColor[1], baseColor[2], 255],
    ],
  });
}

/**
 * Toggle points view mode
 */
function togglePointsMode() {
  if (showPoints) return;
  showPoints = true;
  showHeatmap = false;
  glowCategory = null;
  togglePointsBtn.classList.add('active');
  toggleGlowBtn.classList.remove('active');

  // Restore saved category selections
  visibleCategories = new Set(savedCategories);
  savedCategories.clear();

  updateAllCheckboxStates();
  updateFilteredData();
  renderDeck();
}

/**
 * Toggle heatmap glow mode
 */
function toggleGlowMode() {
  if (showHeatmap) return;
  showHeatmap = true;
  showPoints = false;
  toggleGlowBtn.classList.add('active');
  togglePointsBtn.classList.remove('active');

  // Save current selections before switching
  savedCategories = new Set(visibleCategories);

  // Select only the first top-level category
  const sortedTopLevel = Object.keys(hierarchy).sort((a, b) =>
    hierarchy[b].count - hierarchy[a].count
  );
  const firstCategory = sortedTopLevel[0];
  glowCategory = firstCategory;

  // Update visibleCategories to only this category and its descendants
  visibleCategories.clear();
  const nodeData = hierarchy[firstCategory];
  const descendants = getAllDescendantCategories(nodeData, firstCategory);
  descendants.forEach(d => visibleCategories.add(d));

  updateAllCheckboxStates();
  updateFilteredData();
  renderDeck();
}

/**
 * Handle hover events for tooltips
 */
function handleHover({ object, x, y }) {
  if (object) {
    tooltipEl.innerHTML = `
      <div class="tooltip-name">${escapeHtml(object.name)}</div>
      <div class="tooltip-cuisine">${escapeHtml(object.category)}</div>
      <div class="tooltip-general">${escapeHtml(object.general)}</div>
      <div class="tooltip-address">${escapeHtml(object.address)}, ${escapeHtml(object.boro)}</div>
    `;
    tooltipEl.style.left = `${x + 15}px`;
    tooltipEl.style.top = `${y + 15}px`;
    tooltipEl.classList.add('visible');
  } else {
    tooltipEl.classList.remove('visible');
  }
}

/**
 * Get all categories under a node (recursively), including the node itself
 * This includes all levels, not just leaves, since restaurants can be
 * categorized at any level of the hierarchy
 */
function getAllDescendantCategories(node, name) {
  const categories = [name];  // Include this node
  categories.push(`${name} (Unspecified)`);  // Include "(Unspecified)" variant
  if (node.children) {
    for (const childName in node.children) {
      categories.push(...getAllDescendantCategories(node.children[childName], childName));
    }
  }
  return categories;
}

/**
 * Create a legend item element (for any level)
 */
function createLegendItem(name, data, depth, parentPath) {
  const hasChildren = data.children && Object.keys(data.children).length > 0;
  const isExpanded = expandedGroups.has(name);
  const descendants = getAllDescendantCategories(data, name);
  const allVisible = descendants.every(d => visibleCategories.has(d));
  const someVisible = descendants.some(d => visibleCategories.has(d));

  const itemEl = document.createElement('div');
  itemEl.className = `legend-group depth-${depth}`;
  itemEl.dataset.category = name;
  itemEl.dataset.depth = depth;

  // Header
  const headerEl = document.createElement('div');
  headerEl.className = `legend-group-header${someVisible && !allVisible ? ' partial' : ''}${!someVisible ? ' disabled' : ''}`;
  headerEl.style.paddingLeft = `${depth * 16}px`;

  const checkboxEl = document.createElement('input');
  checkboxEl.type = 'checkbox';
  checkboxEl.checked = allVisible;
  checkboxEl.indeterminate = someVisible && !allVisible;
  checkboxEl.addEventListener('change', (e) => {
    e.stopPropagation();
    toggleCategoryAndDescendants(name, data, e.target.checked);
  });

  const swatchEl = document.createElement('span');
  swatchEl.className = 'legend-swatch';
  swatchEl.style.backgroundColor = rgbToHex(data.color);

  const labelEl = document.createElement('span');
  labelEl.className = 'legend-label';
  labelEl.textContent = name;

  const countEl = document.createElement('span');
  countEl.className = 'legend-count';
  countEl.textContent = data.count.toLocaleString();

  headerEl.appendChild(checkboxEl);
  headerEl.appendChild(swatchEl);
  headerEl.appendChild(labelEl);
  headerEl.appendChild(countEl);

  // Add expand/collapse arrow if there are children
  if (hasChildren) {
    const arrowEl = document.createElement('span');
    arrowEl.className = `legend-arrow${isExpanded ? ' expanded' : ''}`;
    arrowEl.innerHTML = '&#9654;';
    headerEl.appendChild(arrowEl);

    headerEl.style.cursor = 'pointer';
    headerEl.addEventListener('click', (e) => {
      if (e.target.type !== 'checkbox') {
        toggleExpand(name);
      }
    });
  }

  // Legend hover bloom: highlight this category's points on hover (desktop only)
  headerEl.addEventListener('mouseenter', () => {
    if (!showPoints || window.innerWidth <= 768) return;
    legendHoverCategory = name;
    _hoverDescendantsCacheKey = null; // invalidate cache
    pulseStartTime = performance.now();
    startPulseLoop();
  });

  headerEl.addEventListener('mouseleave', () => {
    if (legendHoverCategory === name) {
      legendHoverCategory = null;
      pulseStartTime = null;
      stopPulseLoop();
      renderDeck(); // restore full opacity
    }
  });

  itemEl.appendChild(headerEl);

  // Children (collapsible)
  if (hasChildren) {
    const childrenEl = document.createElement('div');
    childrenEl.className = `legend-specifics${isExpanded ? ' expanded' : ''}`;

    for (const childName of Object.keys(data.children).sort((a, b) =>
      data.children[b].count - data.children[a].count
    )) {
      const childData = data.children[childName];
      childrenEl.appendChild(createLegendItem(childName, childData, depth + 1, [...parentPath, name]));
    }

    itemEl.appendChild(childrenEl);
  }

  return itemEl;
}

/**
 * Toggle a category and all its descendants
 */
function toggleCategoryAndDescendants(name, data, visible) {
  if (showHeatmap) {
    // In glow mode: radio behavior — select only this category
    visibleCategories.clear();
    const descendants = getAllDescendantCategories(data, name);
    descendants.forEach(d => visibleCategories.add(d));
    glowCategory = name;

    updateAllCheckboxStates();
    updateFilteredData();
    renderDeck();
    return;
  }

  const descendants = getAllDescendantCategories(data, name);

  for (const cat of descendants) {
    if (visible) {
      visibleCategories.add(cat);
    } else {
      visibleCategories.delete(cat);
    }
  }

  // Update UI
  updateAllCheckboxStates();
  updateFilteredData();
  renderDeck();
}

/**
 * Update all checkbox states based on visibleCategories
 */
function updateAllCheckboxStates() {
  function updateNode(el) {
    const category = el.dataset.category;
    if (!category) return;

    // Find the node data in hierarchy
    const nodeData = findNodeInHierarchy(category);
    if (!nodeData) return;

    const descendants = getAllDescendantCategories(nodeData, category);
    const allVisible = descendants.every(d => visibleCategories.has(d));
    const someVisible = descendants.some(d => visibleCategories.has(d));

    const header = el.querySelector(':scope > .legend-group-header');
    const checkbox = header?.querySelector('input[type="checkbox"]');

    if (checkbox) {
      checkbox.checked = allVisible;
      checkbox.indeterminate = someVisible && !allVisible;
    }

    if (header) {
      header.classList.toggle('disabled', !someVisible);
      header.classList.toggle('partial', someVisible && !allVisible);
    }
  }

  legendItemsEl.querySelectorAll('.legend-group').forEach(updateNode);
}

/**
 * Find a node in the hierarchy by name
 */
function findNodeInHierarchy(name) {
  function search(nodes) {
    for (const nodeName in nodes) {
      if (nodeName === name) return nodes[nodeName];
      if (nodes[nodeName].children) {
        const found = search(nodes[nodeName].children);
        if (found) return found;
      }
    }
    return null;
  }
  return search(hierarchy);
}

/**
 * Set up the legend with collapsible category groups
 */
function setupLegend() {
  legendItemsEl.innerHTML = '';

  // Sort top-level categories by count
  const sortedTopLevel = Object.keys(hierarchy).sort((a, b) =>
    hierarchy[b].count - hierarchy[a].count
  );

  for (const topLevel of sortedTopLevel) {
    const groupData = hierarchy[topLevel];
    legendItemsEl.appendChild(createLegendItem(topLevel, groupData, 0, []));
  }

  // Select all/none buttons
  selectAllBtn.addEventListener('click', selectAll);
  selectNoneBtn.addEventListener('click', selectNone);

  // View mode toggles
  togglePointsBtn.addEventListener('click', togglePointsMode);
  toggleGlowBtn.addEventListener('click', toggleGlowMode);
}

/**
 * Toggle expand/collapse of a group
 */
function toggleExpand(category) {
  if (expandedGroups.has(category)) {
    expandedGroups.delete(category);
  } else {
    expandedGroups.add(category);
  }

  const groupEl = legendItemsEl.querySelector(`[data-category="${category}"]`);
  if (groupEl) {
    const arrow = groupEl.querySelector(':scope > .legend-group-header .legend-arrow');
    const children = groupEl.querySelector(':scope > .legend-specifics');

    if (arrow) arrow.classList.toggle('expanded');
    if (children) children.classList.toggle('expanded');
  }
}

/**
 * Select all categories
 */
function selectAll() {
  // Get all leaf categories recursively
  function collectAllLeaves(nodes) {
    for (const name in nodes) {
      const node = nodes[name];
      const descendants = getAllDescendantCategories(node, name);
      descendants.forEach(d => visibleCategories.add(d));
    }
  }
  collectAllLeaves(hierarchy);

  // Update UI
  legendItemsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.checked = true;
    cb.indeterminate = false;
  });
  legendItemsEl.querySelectorAll('.legend-group-header').forEach(el => {
    el.classList.remove('disabled', 'partial');
  });

  updateFilteredData();
  renderDeck();
}

/**
 * Select no categories
 */
function selectNone() {
  visibleCategories.clear();

  // Update UI
  legendItemsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.checked = false;
    cb.indeterminate = false;
  });
  legendItemsEl.querySelectorAll('.legend-group-header').forEach(el => {
    el.classList.add('disabled');
    el.classList.remove('partial');
  });

  updateFilteredData();
  renderDeck();
}

/**
 * Update the restaurant count display
 */
function updateRestaurantCount() {
  const visible = filteredData.length;
  const total = allData.length;
  restaurantCountEl.textContent = `${visible.toLocaleString()} of ${total.toLocaleString()} restaurants`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Mobile legend drawer toggle
document.getElementById('legend-drag-handle').addEventListener('click', () => {
  document.getElementById('legend').classList.toggle('legend-expanded');
});

// Start the application
init();
