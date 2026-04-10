# Quick Road Network Path AI (QGIS Plugin)

## Overview

**Quick Road Network Path AI** is a QGIS plugin that calculates the **fastest path between two user-defined points on a road network** using the **A* (A-star) pathfinding algorithm**.

The plugin dynamically converts a road network into a graph structure, snaps user-selected points to the nearest valid road geometry, and computes an optimal route based on **travel time**. The resulting path is displayed as a temporary layer and can be exported in multiple formats.

---

## Features

* Select a **road network layer** (line geometry).
* Optional **boundary layer filtering** to constrain routing.
* Interactive selection of **start and end points** on the map.
* Automatic snapping of points to the nearest road segment.
* Fast route computation using **A*** algorithm.
* Outputs:

  * Total **distance (km)**
  * Estimated **travel time (minutes)**
* Creates a temporary route layer with attributes:

  * `id`
  * `length_km`
  * `time_min`
* Export results to:

  * GeoPackage (.gpkg)
  * Shapefile (.shp)
  * Custom file location

---

## How It Works

### 1. Input Selection

* User selects:

  * A **road layer** (required)
  * A **boundary layer** (optional)
* User clicks two points on the map:

  * Start point
  * End point

---

### 2. Snapping

Each clicked point is snapped to the nearest road geometry:

* Uses `QgsGeometry.nearestPoint()`
* Distance is calculated using `QgsDistanceArea`
* A maximum snapping threshold is applied:

```
max_snap_distance_m = 1000
```

If no road is found within this distance, the process stops with a warning.

---

### 3. Graph Construction

The road network is converted into a graph:

* **Nodes**: road vertices
* **Edges**: segments between vertices

Each edge stores:

* Length (km)
* Travel time (minutes)

Travel time is computed as:

```
time = (distance / speed) * 60
```

* If a `speed` field exists → it is used
* Otherwise → default speed = **50 km/h**

---

### 4. Pathfinding (A* Algorithm)

The plugin uses the **A*** algorithm to compute the optimal route.

* Cost function → **travel time**
* Heuristic → Euclidean distance:

```
h(n) = sqrt((x2 - x1)^2 + (y2 - y1)^2)
```

This ensures:

* Efficient search
* Optimal solution (fastest path)

---

### 5. Output Layer

The resulting path is:

* Created as a **temporary LineString layer**
* Added automatically to the QGIS project
* Contains:

  * Total distance
  * Total travel time

---

### 6. Export

Users can export the result via dialog:

* GeoPackage (default temp file)
* Shapefile
* Custom path

---

## Requirements

* QGIS 3.x
* Python 3.x (included with QGIS)

### Input Data Requirements

**Road Layer:**

* Geometry: LineString / MultiLineString
* Must be **topologically connected**

**Optional:**

* `speed` field (numeric, km/h)

---

## Installation

1. Clone or download the repository:

```
git clone https://github.com/your-username/your-repo.git
```

2. Copy the plugin folder into your QGIS plugin directory:

**Windows:**

```
C:\Users\<YourUser>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```

**Linux:**

```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**macOS:**

```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

3. Restart QGIS

4. Enable the plugin:

* Plugins → Manage and Install Plugins → Installed → Enable

---

## Usage

### 1. Prepare Data

* Load a road network layer
* (Optional) Load a boundary polygon layer

---

### 2. Run Plugin

* Go to:

```
Plugins → Quick Road Network Path AI
```

---

### 3. Set Parameters

* Select:

  * Road Layer
  * Optional Boundary Layer

* Click:

```
Pick Start and End Points
```

---

### 4. Select Points

* Click on map:

  * First click → Start point
  * Second click → End point

---

### 5. Results

* Route is displayed on map
* Export dialog appears
* Choose format to save

---

## Messages & Error Handling

The plugin provides feedback via dialogs:

**Warnings:**

* No road layer selected
* Failed snapping (no nearby road)
* No path found

**Information:**

* Instructions for selecting points
* Export confirmation

---

## Limitations & Notes

* Assumes **bidirectional roads**
* No support for:

  * One-way streets
  * Turn restrictions
  * Traffic data
* Graph is rebuilt every run (can be slow for large datasets)
* Snapping uses linear search (can be optimized with spatial index)

---

## Code Structure

### Main Class

```
QuickRoadNetworkPathAI
```

### Key Components

* **GUI**

  * `initGui()`
  * `create_dock()`

* **User Interaction**

  * `pick_points()`
  * `get_point_from_map()`

* **Processing**

  * `snap_to_road()`
  * `build_graph()`
  * `a_star()`

* **Output**

  * `create_route_layer()`
  * `export_*()`

---

## License

This plugin is released under the **GNU General Public License v3.0 (GPLv3)**.

---

## Support and Contribution

* Author: *Dimitra Pappa*
* Repository: https://github.com/demetrapappa14-geospatial/quickRoadNetworkPathAI
* Issues: Use GitHub Issues for bug reports and feature requests

Contributions are welcome via pull requests.
