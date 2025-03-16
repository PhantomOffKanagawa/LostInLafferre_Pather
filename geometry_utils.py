import numpy as np
from shapely.geometry import Polygon, LineString, MultiLineString, Point, GeometryCollection
import pygeoops
from xml.etree import ElementTree as ET

def shapely_to_pygame(shape):
    """
    Converts a Shapely LineString or MultiLineString into a pygame-readable list of points.

    Parameters:
        shape: A Shapely LineString, MultiLineString, or GeometryCollection

    Returns:
        A list of tuples for LineString or a list of lists of tuples for MultiLineString
    """
    if isinstance(shape, LineString):
        return list(shape.coords)
    elif isinstance(shape, MultiLineString):
        return [list(line.coords) for line in shape.geoms]  # Use .geoms to iterate sub-lines
    elif isinstance(shape, GeometryCollection):
        return [shapely_to_pygame(geom) for geom in shape.geoms]
    else:
        raise TypeError("Input must be a LineString, MultiLineString, or GeometryCollection")


def find_midline_path(polygon):
    """
    Finds the midline path of a polygon using pygeoops.centerline.
    
    Parameters:
        polygon: A list of (x, y) tuples representing polygon vertices
        
    Returns:
        A list of points representing the midline path
    """
    # Convert the polygon to a shapely Polygon object
    shapely_polygon = Polygon(polygon)
    
    # Calculate the centerline using pygeoops
    centerline = pygeoops.centerline(shapely_polygon, extend=False, densify_distance=5, simplifytolerance=0.5, min_branch_length=-1)
    
    # Extract the coordinates of the centerline
    midline_points = shapely_to_pygame(centerline)
    
    return midline_points

def transform_point(point, scale, offset):
    """
    Transforms a single point by scaling and offsetting.
    
    Parameters:
        point: An (x, y) tuple
        scale: Scale factor
        offset: (offset_x, offset_y) tuple
        
    Returns:
        Transformed (x, y) tuple
    """
    x, y = point
    return (x * scale + offset[0], y * scale + offset[1])

def inverse_transform_point(point, scale, offset):
    """
    Inverse transforms a single point by scaling and offsetting.
    
    Parameters:
        point: An (x, y) tuple
        scale: Scale factor
        offset: (offset_x, offset_y) tuple
        
    Returns:
        Original (x, y) tuple
    """
    x, y = point
    return ((x - offset[0]) / scale, (y - offset[1]) / scale)

def transform_shapes(shapes, scale, offset):
    """
    Transforms multiple shapes by scaling and offsetting.
    
    Parameters:
        shapes: List of shapes (each shape is a list of points)
        scale: Scale factor
        offset: (offset_x, offset_y) tuple
        
    Returns:
        List of transformed shapes
    """
    transformed_shapes = []
    for shape in shapes:
        transformed_shape = [transform_point(p, scale, offset) for p in shape]
        transformed_shapes.append(transformed_shape)
    return transformed_shapes

def zoom_at(scale, offset, mouse_pos, zoom_factor):
    """
    Zooms in or out centered at the mouse position.
    
    Parameters:
        scale: Current scale factor
        offset: Current (offset_x, offset_y) tuple
        mouse_pos: Mouse position (x, y)
        zoom_factor: Factor by which to zoom (>1 to zoom in, <1 to zoom out)
        
    Returns:
        New scale and offset
    """
    mx, my = mouse_pos
    offset[0] = mx - (mx - offset[0]) * zoom_factor
    offset[1] = my - (my - offset[1]) * zoom_factor
    scale *= zoom_factor
    return scale, offset

def is_point_near_line(point, line_points, threshold=5):
    """
    Checks if a point is near a polyline segment.
    
    Parameters:
        point: (x, y) tuple
        line_points: List of (x, y) tuples forming a polyline
        threshold: Maximum distance to be considered "near"
        
    Returns:
        Boolean indicating if point is near the line
    """
    px, py = point
    for i in range(len(line_points) - 1):
        x1, y1, x2, y2 = *line_points[i], *line_points[i + 1]
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            continue
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        closest_x, closest_y = x1 + t * dx, y1 + t * dy
        if ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5 < threshold:
            return True
    return False

def nearest_point_on_line(point, lines):
    """
    Finds the nearest point on a line or lines from a given point.
    
    Parameters:
        point: (x, y) tuple
        lines: Either a list of (x, y) tuples or a list of lists of (x, y) tuples
        
    Returns:
        The nearest point (x, y) on the line(s)
    """
    if isinstance(lines, list) and all(isinstance(line, list) for line in lines):
        nearest_point = None
        min_distance = float('inf')
        
        for line in lines:
            for l_point in line:
                distance = ((point[0] - l_point[0]) ** 2 + (point[1] - l_point[1]) ** 2) ** 0.5
            
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = l_point
    else:
        nearest_point = None
        min_distance = float('inf')
        
        for l_point in lines:
            distance = ((point[0] - l_point[0]) ** 2 + (point[1] - l_point[1]) ** 2) ** 0.5
        
            if distance < min_distance:
                min_distance = distance
                nearest_point = l_point
    
    return nearest_point

def is_point_inside_polygon(point, polygon, tolerance=0):
    """
    Ray-casting algorithm for point-in-polygon detection with optional tolerance.
    
    Parameters:
        point: (x, y) tuple
        polygon: List of (x, y) tuples forming a polygon
        tolerance: Distance tolerance for points near the polygon edge
        
    Returns:
        Boolean indicating if point is inside or within tolerance of the polygon
    """
    px, py, inside = *point, False
    n = len(polygon)
    for i in range(n):
        x1, y1, x2, y2 = *polygon[i], *polygon[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1):
            inside = not inside
    if inside:
        return True
    # Check if the point is within the tolerance distance from the polygon edges
    for i in range(n):
        x1, y1, x2, y2 = *polygon[i], *polygon[(i + 1) % n]
        if is_point_near_line(point, [(x1, y1), (x2, y2)], threshold=tolerance):
            return True
    return False

def find_innermost_polygon(mouse_pos, shapes):
    """
    Finds the innermost polygon that contains the mouse position.
    
    Parameters:
        mouse_pos: (x, y) tuple
        shapes: List of polygons (each polygon is a list of points)
        
    Returns:
        The innermost polygon containing the mouse position, or None if no polygon contains it
    """
    innermost_shape = None
    innermost_area = float('inf')
    for shape in shapes:
        if is_point_inside_polygon(mouse_pos, shape):
            area = polygon_area(shape)
            if area < innermost_area:
                innermost_area = area
                innermost_shape = shape
    return innermost_shape

def polygon_area(polygon):
    """
    Calculates the area of a polygon using the Shoelace formula.
    
    Parameters:
        polygon: List of (x, y) tuples forming a polygon
        
    Returns:
        Area of the polygon
    """
    n = len(polygon)
    area = 0.0
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0

def export_polyline(points):
    """Creates an SVG polyline element with the given points and color."""
    polyline = ET.Element('polyline', points=" ".join(f"{x},{y}" for x, y in points))
    # polyline.set('style', f"fill:none;stroke:rgb{color};stroke-width:2")
    return polyline

def export_polygon(points):
    """Creates an SVG polygon element with the given points and color."""
    polygon = ET.Element('polygon', points=" ".join(f"{x},{y}" for x, y in points))
    # polygon.set('style', f"fill:none;stroke:rgb{color};stroke-width:2")
    return polygon