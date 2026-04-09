# Quick Road Network Path AI

![QGIS version](https://img.shields.io/badge/QGIS-3.x-green)
![Python version](https://img.shields.io/badge/Python-3.x-yellow)
![License](https://img.shields.io/badge/license-GPLv3-blue)

**Quick Road Network Path AI** is a QGIS plugin for quickly calculating and visualizing the **shortest path along road networks**. It automatically snaps points to roads, supports optional boundary layers, and exports results in multiple formats.

---

## Features

- Select any road vector layer.  
- Optional boundary layer filtering.  
- Pick start and end points interactively on the map.  
- Snap points to nearest road automatically.  
- Shortest path calculation using **A*** algorithm.  
- Displays route with distance and estimated travel time.  
- Export route as GeoPackage, Shapefile, or custom path.  

---

## Screenshots

![Dock panel](images/dock_panel.png)  
*Dock panel for selecting layers and picking points.*

![Shortest path](images/shortest_path.png)  
*Shortest path displayed on the map with start (green) and end (red) markers.*

---

## Installation

1. Copy the `QuickRoadNetworkPathAI` folder into your QGIS plugins directory:  

   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`  
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`  
   - **Mac**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`  

2. Restart QGIS.  
3. Go to **Plugins → Manage and Install Plugins…**  
4. Enable **Quick Road Network Path AI**.  

---

## Usage

1. Click **Quick Road Network Path AI** in the **Plugins menu**.  
2. The dock panel opens.  
3. Select the **Road Layer** (and optional **Boundary Layer**).  
4. Click **Pick Start and End Points**.  
5. Click on the map to select the start and end points.  
6. The shortest path is calculated and displayed.  
7. Export the route via the dialog (GeoPackage, Shapefile, or custom path).  

---

## Optional Configuration

- **Max snapping distance**: 1000 meters (default, adjustable in the code).  
- **Speed attribute**: Reads `speed` from the road layer; defaults to 50 km/h if missing.  

---

## Troubleshooting

- **No path found**: Ensure the road layer geometry is correct and points are within layer bounds.  
- **Points not snapping**: Check the **max_snap_distance_m** value and that roads are close enough.  
- **Export issues**: Ensure write permissions and that no existing files are open.  

---

## Contributing

1. Fork the repository.  
2. Create a branch (`git checkout -b feature-name`).  
3. Make your changes.  
4. Commit (`git commit -m "Add feature"`).  
5. Push to your branch (`git push origin feature-name`).  
6. Open a Pull Request.  

---

## License

This plugin is licensed under the **GNU General Public License v3.0 (GPLv3)**.  

For full license text, see [LICENSE](LICENSE) or [https://www.gnu.org/licenses/gpl-3.0.en.html](https://www.gnu.org/licenses/gpl-3.0.en.html).