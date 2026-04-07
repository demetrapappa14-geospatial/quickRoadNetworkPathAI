from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QDockWidget, QWidget, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QFileDialog
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsDistanceArea, QgsVectorLayerExporter,
    QgsFields, QgsField, QgsCoordinateTransform,
    QgsSpatialIndex
)
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker
import heapq
import math
import os
import tempfile

class QuickRoadNetworkPathAI:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.start_point = None
        self.end_point = None
        self.start_marker = None
        self.end_marker = None
        self.route_layer = None
        self.action = None
        self.map_tool = None
        self.dock = None
        self.road_layer = None
        self.boundary_layer = None
        self.max_snap_distance_m = 1000.0  # max snapping distance

    # ---------------- GUI ----------------
    def initGui(self):
        self.action = QAction("Quick Road Network Path AI", self.iface.mainWindow())
        self.action.triggered.connect(self.create_dock)
        self.iface.addPluginToMenu("Quick Road Network Path AI", self.action)

    def unload(self):
        self.iface.removePluginMenu("Quick Road Network Path AI", self.action)
        if self.dock:
            try:
                self.iface.removeDockWidget(self.dock)
            except RuntimeError:
                pass
            self.dock.deleteLater()
            self.dock = None
        self.clear_markers()
        self.clear_route()

    # ---------------- Dock Panel ----------------
    def create_dock(self):
        self.dock = QDockWidget("Quick Road Network Path AI", self.iface.mainWindow())
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Road Layer:"))
        self.road_combo = QComboBox()
        layout.addWidget(self.road_combo)

        layout.addWidget(QLabel("Optional Boundary Layer:"))
        self.boundary_combo = QComboBox()
        layout.addWidget(self.boundary_combo)

        self.start_button = QPushButton("Pick Start and End Points")
        layout.addWidget(self.start_button)

        widget.setLayout(layout)
        self.dock.setWidget(widget)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        layers = [l for l in QgsProject.instance().mapLayers().values() if l.type() == QgsVectorLayer.VectorLayer]
        self.road_combo.clear()
        self.boundary_combo.clear()
        self.boundary_combo.addItem("None")
        for layer in layers:
            self.road_combo.addItem(layer.name())
            self.boundary_combo.addItem(layer.name())

        self.start_button.clicked.connect(self.pick_points)

    # ---------------- Pick Points ----------------
    def pick_points(self):
        self.clear_markers()
        self.clear_route()

        road_name = self.road_combo.currentText()
        self.road_layer = next((l for l in QgsProject.instance().mapLayers().values() if l.name() == road_name), None)
        if not self.road_layer:
            QMessageBox.warning(None, "Error", "No road layer selected.")
            return

        boundary_name = self.boundary_combo.currentText()
        self.boundary_layer = None if boundary_name == "None" else next((l for l in QgsProject.instance().mapLayers().values() if l.name() == boundary_name), None)

        QMessageBox.information(None, "Start Point", "Click on the map to set the START point")
        self.start_button.setEnabled(False)
        self.get_point_from_map(self.on_start_point_picked)

    def get_point_from_map(self, callback):
        self.map_tool = QgsMapToolEmitPoint(self.canvas)

        def on_click(point, button):
            try:
                self.map_tool.canvasClicked.disconnect(on_click)
            except Exception:
                pass
            self.canvas.unsetMapTool(self.map_tool)
            callback(point)

        self.map_tool.canvasClicked.connect(on_click)
        self.canvas.setMapTool(self.map_tool)

    # ---------------- Snapping ----------------
    def snap_to_road(self, map_point):
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        layer_crs = self.road_layer.crs()
        transform_to_layer = QgsCoordinateTransform(canvas_crs, layer_crs, QgsProject.instance().transformContext())
        pt_layer_crs = transform_to_layer.transform(map_point)

        # Optional boundary filtering
        features = self.road_layer.getFeatures()
        if self.boundary_layer:
            boundary_geom = [f.geometry() for f in self.boundary_layer.getFeatures()]
            features = [f for f in features if any(f.geometry().intersects(b) for b in boundary_geom)]

        da = QgsDistanceArea()
        da.setSourceCrs(layer_crs, QgsProject.instance().transformContext())
        da.setEllipsoid('WGS84')

        nearest_point = None
        min_dist = float("inf")
        for feat in features:
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            nearest_geom = geom.nearestPoint(QgsGeometry.fromPointXY(pt_layer_crs))
            if nearest_geom is None or nearest_geom.isEmpty():
                continue
            candidate = nearest_geom.asPoint()
            d = da.measureLine(pt_layer_crs, QgsPointXY(candidate))
            if d < min_dist:
                min_dist = d
                nearest_point = QgsPointXY(candidate)

        if nearest_point and self.max_snap_distance_m and min_dist > self.max_snap_distance_m:
            QMessageBox.warning(None, "Snapping", f"No nearby road found within {self.max_snap_distance_m} m.")
            return None
        return nearest_point

    # ---------------- Start / End ----------------
    def on_start_point_picked(self, map_point):
        snapped = self.snap_to_road(map_point)
        if snapped is None:
            QMessageBox.warning(None, "Error", "Could not snap start point.")
            self.start_button.setEnabled(True)
            return
        self.start_point = snapped
        self.show_marker(snapped, Qt.green)
        QMessageBox.information(None, "End Point", "Click on the map to set the END point")
        self.get_point_from_map(self.on_end_point_picked)

    def on_end_point_picked(self, map_point):
        snapped = self.snap_to_road(map_point)
        if snapped is None:
            QMessageBox.warning(None, "Error", "Could not snap end point.")
            self.start_button.setEnabled(True)
            return
        self.end_point = snapped
        self.show_marker(snapped, Qt.red)
        self.calculate_shortest_path()
        self.start_button.setEnabled(True)

    # ---------------- Show Marker ----------------
    def show_marker(self, point, color):
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        layer_crs = self.road_layer.crs()
        transform = QgsCoordinateTransform(layer_crs, canvas_crs, QgsProject.instance().transformContext())
        display_point = transform.transform(point)

        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(display_point)
        marker.setColor(color)
        marker.setIconSize(12)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setPenWidth(3)

        if color == Qt.green:
            self.start_marker = marker
        else:
            self.end_marker = marker

    # ---------------- Clear ----------------
    def clear_markers(self):
        for marker in [self.start_marker, self.end_marker]:
            if marker:
                try:
                    self.canvas.scene().removeItem(marker)
                except Exception:
                    pass
        self.start_marker = None
        self.end_marker = None

    def clear_route(self):
        if self.route_layer:
            try:
                QgsProject.instance().removeMapLayer(self.route_layer)
            except Exception:
                pass
            self.route_layer = None

    # ---------------- Graph Helpers ----------------
    def build_graph(self, road_layer):
        da = QgsDistanceArea()
        da.setSourceCrs(road_layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid('WGS84')
        nodes = []
        edges = {}
        node_index_map = {}
        idx = 0
        for feat in road_layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            lines = geom.asMultiPolyline() if geom.isMultipart() else [geom.asPolyline()]
            speed = float(feat["speed"]) if "speed" in feat.fields().names() else 50.0
            for line in lines:
                for i in range(len(line)-1):
                    p1 = line[i]
                    p2 = line[i+1]
                    for p in [p1, p2]:
                        key = (round(p.x(),6), round(p.y(),6))
                        if key not in node_index_map:
                            node_index_map[key] = idx
                            nodes.append(p)
                            edges[idx] = []
                            idx +=1
                    id1 = node_index_map[(round(p1.x(),6), round(p1.y(),6))]
                    id2 = node_index_map[(round(p2.x(),6), round(p2.y(),6))]
                    length_km = da.measureLine(p1,p2)/1000
                    if length_km <= 0: continue
                    time_min = (length_km/speed)*60
                    edges[id1].append((id2,length_km,time_min))
                    edges[id2].append((id1,length_km,time_min))
        return nodes, edges

    def find_nearest_node(self, point, nodes):
        return min(range(len(nodes)), key=lambda i: (nodes[i].x()-point.x())**2 + (nodes[i].y()-point.y())**2)

    def heuristic(self, a, b):
        return math.hypot(a.x()-b.x(), a.y()-b.y())

    def a_star(self, nodes, edges, start, goal):
        open_set = [(0,start)]
        came_from = {}
        g = {i: float('inf') for i in range(len(nodes))}
        g[start] = 0
        f = {i: float('inf') for i in range(len(nodes))}
        f[start] = self.heuristic(nodes[start], nodes[goal])
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path=[]
                total_time=0
                total_distance=0
                c=goal
                while c in came_from:
                    p = came_from[c]
                    for n,l,t in edges[p]:
                        if n==c:
                            total_time += t
                            total_distance += l
                            break
                    path.insert(0,c)
                    c=p
                path.insert(0,start)
                return path, total_time, total_distance
            for neighbor,l,t in edges.get(current,[]):
                tg = g[current]+t
                if tg < g[neighbor]:
                    came_from[neighbor]=current
                    g[neighbor]=tg
                    f[neighbor]=tg+self.heuristic(nodes[neighbor], nodes[goal])
                    heapq.heappush(open_set,(f[neighbor], neighbor))
        return None,None,None

    # ---------------- Calculate Shortest Path ----------------
    def calculate_shortest_path(self):
        nodes, edges = self.build_graph(self.road_layer)
        if not nodes or self.start_point is None or self.end_point is None:
            QMessageBox.warning(None, "Error", "Cannot calculate path.")
            return
        start_node = self.find_nearest_node(self.start_point, nodes)
        end_node = self.find_nearest_node(self.end_point, nodes)
        path, total_time, total_distance = self.a_star(nodes, edges, start_node, end_node)
        if not path:
            QMessageBox.warning(None, "Error", "No path found.")
            return
        self.route_layer = self.create_route_layer(path, nodes, total_distance, total_time, self.road_layer.crs())
        self.zoom_to_route(self.route_layer)
        self.export_result_dialog(self.route_layer, total_distance, total_time)

    # ---------------- Route Layer & Zoom ----------------
    def create_route_layer(self, path, nodes, dist, time, crs):
        fields = QgsFields()
        fields.append(QgsField("id",QVariant.Int))
        fields.append(QgsField("length_km",QVariant.Double))
        fields.append(QgsField("time_min",QVariant.Double))
        layer = QgsVectorLayer(f"LineString?crs={crs.authid()}","shortest_route_ai","memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields)
        layer.updateFields()
        line_points = [nodes[i] for i in path]
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromPolylineXY(line_points))
        feat["id"]=1
        feat["length_km"]=dist
        feat["time_min"]=time
        pr.addFeature(feat)
        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)
        return layer

    def zoom_to_route(self, layer):
        if layer is None:
            return
        # Zoom to the actual route geometry
        extent = layer.extent()
        self.canvas.setExtent(extent)
        self.canvas.refresh()

    # ---------------- Export ----------------
    def export_result_dialog(self, route_layer, dist, time):
        msg = QMessageBox()
        msg.setWindowTitle("Export Route")
        msg.setText(f"Shortest path found!\nDistance: {dist:.2f} km\nTime: {time:.1f} min\n\nChoose export format:")
        gpkg_btn = msg.addButton("GeoPackage", QMessageBox.AcceptRole)
        shp_btn = msg.addButton("Shapefile", QMessageBox.AcceptRole)
        custom_btn = msg.addButton("Custom Path", QMessageBox.AcceptRole)
        cancel = msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton()==gpkg_btn:
            self.export_gpkg(route_layer)
        elif msg.clickedButton()==shp_btn:
            self.export_shapefile(route_layer)
        elif msg.clickedButton()==custom_btn:
            self.export_custom_path(route_layer)

    def export_gpkg(self, layer):
        path=os.path.join(tempfile.gettempdir(),"quick_route_ai.gpkg")
        if os.path.exists(path): os.remove(path)
        options={"layerName":"route"}
        error=QgsVectorLayerExporter.exportLayer(layer,path,"GPKG",layer.crs(),options=options)
        if error[0]!=QgsVectorLayerExporter.NoError:
            QMessageBox.warning(None,"Error",str(error[1]))
            return
        new_layer=QgsVectorLayer(f"{path}|layername=route","Quick Route AI","ogr")
        QgsProject.instance().addMapLayer(new_layer)
        QMessageBox.information(None,"Saved",f"Saved to:\n{path}")

    def export_shapefile(self, layer):
        path=os.path.join(tempfile.gettempdir(),"quick_route_ai.shp")
        for ext in ["shp","shx","dbf","prj","cpg"]:
            f=path.replace(".shp",f".{ext}")
            if os.path.exists(f): os.remove(f)
        error=QgsVectorLayerExporter.exportLayer(layer,path,"ESRI Shapefile",layer.crs(),options={"fileEncoding":"UTF-8"})
        if error[0]!=QgsVectorLayerExporter.NoError:
            QMessageBox.warning(None,"Error",str(error[1]))
            return
        new_layer=QgsVectorLayer(path,"Quick Route AI","ogr")
        QgsProject.instance().addMapLayer(new_layer)
        QMessageBox.information(None,"Saved",f"Saved to:\n{path}")

    def export_custom_path(self, layer):
        filename,_=QFileDialog.getSaveFileName(None,"Save Route","","GeoPackage (*.gpkg);;Shapefile (*.shp)")
        if not filename: return
        if filename.endswith(".shp"):
            driver="ESRI Shapefile"
        else:
            if not filename.endswith(".gpkg"): filename+=".gpkg"
            driver="GPKG"
        options = {"layerName":"route"} if driver=="GPKG" else {"fileEncoding":"UTF-8"}
        error=QgsVectorLayerExporter.exportLayer(layer,filename,driver,layer.crs(),options=options)
        if error[0]!=QgsVectorLayerExporter.NoError:
            QMessageBox.warning(None,"Error",str(error[1]))
            return
        layer_loaded=QgsVectorLayer(filename,"Quick Route AI","ogr")
        if not layer_loaded.isValid():
            QMessageBox.warning(None,"Error",f"Failed to load layer:\n{filename}")
            return
        QgsProject.instance().addMapLayer(layer_loaded)
        QMessageBox.information(None,"Done",f"Saved:\n{filename}")
