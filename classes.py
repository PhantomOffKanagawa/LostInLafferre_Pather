import pygame
from geometry_utils import find_innermost_polygon, transform_point, is_point_inside_polygon
from typing import Type
from values import Colors, Constants, KeyBindings
from geometry_utils import export_polygon, export_polyline, export_point
import xml.etree.ElementTree as ET

class MapElement:
    """Base class for all map elements"""
    def __init__(self, position, element_id=1):
        self.position = position  # (x, y) tuple
        self.id = element_id
        self.selected = False
        self.color = None
    
    def is_clicked(self, point, scale, offset):
        """Check if the element is clicked (base implementation)"""
        # To be overridden by subclasses
        return False
        
    def draw(self, screen, scale, offset):
        """Draw the element (base implementation)"""
        # To be overridden by subclasses
        pass
    
    def export(self):
        """Export the element as SVG (base implementation)"""
        # To be overridden by subclasses
        return None, None
    
    def set_selected(self, selected):
        """Set the selected state of the element"""
        self.selected = selected

class Elevator(MapElement):
    """Elevator element for connecting floors"""
    def __init__(self, position, elevator_id=1):
        super().__init__(position, elevator_id)
        self.radius = Constants.DEFAULT_RADIUS  # Radius for drawing
        self.color = Colors.ELEVATOR  # Default color for elevator

    def is_clicked(self, point, scale, offset):
        # Check if a point is within the elevator's circle
        x1, y1 = self.position
        x2, y2 = point
        x1, y1 = transform_point((x1, y1), scale, offset)
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        return distance <= self.radius * scale

    def draw(self, screen, scale, offset):
        # Draw elevator circle
        x, y = transform_point(self.position, scale, offset)
        color = Colors.ELEVATOR_SELECTED if self.selected else Colors.ELEVATOR
        pygame.draw.circle(screen, color, (int(x), int(y)), int(self.radius * scale))
        
        # Draw elevator ID text
        font = pygame.font.SysFont(Constants.DEFAULT_FONT, int(12 * scale))
        text = font.render(str(self.id), True, Colors.TEXT)
        text_rect = text.get_rect(center=(int(x), int(y)))
        screen.blit(text, text_rect)

    def export(self):
        """Creates an SVG circle element at the specified position with the given radius and color."""
        cx, cy = self.position
        attrs = {
            'cx': str(cx),
            'cy': str(cy),
            'r': str(self.radius),
            'adjacency': str(self.id),
            'data-id': str(self.id),
            'data-type': 'elevator'
        }
        
        circle = ET.Element('circle', **attrs)
        
        # Create text element for the ID
        text_attrs = {
            'x': str(cx),
            'y': str(cy),
            'text-anchor': 'middle',
            'dy': '.3em',  # Adjust vertical alignment
            'style': 'font-size:12px; fill: white;'
        }
        text = ET.Element('text', **text_attrs)
        text.text = str(self.id)
        
        return (circle, text)

class Stairs(MapElement):
    """Stairs element for connecting floors"""
    def __init__(self, position, stairs_id=1):
        super().__init__(position, stairs_id)
        self.radius = Constants.DEFAULT_RADIUS  # Radius for drawing
        self.color = Colors.STAIRS  # Default color for stairs
    
    def is_clicked(self, point, scale, offset):
        # Check if a point is within the stairs' area (assuming a rectangular area)
        x1, y1 = self.position
        x2, y2 = point
        x1, y1 = transform_point((x1, y1), scale, offset)
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        return distance <= self.radius * 2 * scale

    def draw(self, screen, scale, offset):
        # Draw stairs rectangle
        x, y = transform_point(self.position, scale, offset)
        width, height = self.radius * 2 * scale, self.radius * 2 * scale
        color = Colors.STAIRS_SELECTED if self.selected else Colors.STAIRS
        pygame.draw.rect(screen, color, (int(x - width / 2), int(y - height / 2), int(width), int(height)))
        
        # Draw stairs ID text
        font = pygame.font.SysFont(Constants.DEFAULT_FONT, int(12 * scale))
        text = font.render(str(self.id), True, Colors.TEXT)
        text_rect = text.get_rect(center=(int(x), int(y)))
        screen.blit(text, text_rect)

    def export(self):
        """Creates an SVG circle element at the specified position with the given width, height, and color."""
        cx, cy = self.position
        attrs = {
            'cx': str(cx),
            'cy': str(cy),
            'r': str(self.radius),
            'adjacency': str(self.id),
            'data-id': str(self.id),
            'data-type': 'stairs'
        }
        
        circle = ET.Element('circle', **attrs)
        
        # Create text element for the ID
        text_attrs = {
            'x': str(cx),
            'y': str(cy),
            'text-anchor': 'middle',
            'dy': '.3em',  # Adjust vertical alignment
            'style': 'font-size:12px; fill: white;'
        }
        text = ET.Element('text', **text_attrs)
        text.text = str(self.id)
        
        return (circle, text)

class Space():
    """Space element (room, corridor, etc.)"""
    def __init__(self, polygon_points, space_id=0):
        self.points = polygon_points  # List of points forming the polygon
        self.id = space_id
        self.selected = False
        self.name = None  # Name of the space (if named)
        self.color = Colors.SPACE  # Default color for space
        self.name_points = None  # Points for the name (if applicable)
    
    def set_selected(self, selected):
        self.selected = selected
    
    def draw(self, screen, scale, offset):
        # Transform points for drawing
        transformed_points = [transform_point(p, scale, offset) for p in self.points]
        # Draw polygon
        color = Colors.HIGHLIGHT if self.selected else Colors.SPACE
        pygame.draw.polygon(screen, color, transformed_points)
        # Draw name if applicable
        if self.name and self.name_points:
            transformed_name_points = transform_point(self.name_points, scale, offset)
            # Calculate center of the space
            center_x = transformed_name_points[0]
            center_y = transformed_name_points[1]
            
            font = pygame.font.SysFont(Constants.DEFAULT_FONT, 14)
            text = font.render(self.name, True, Colors.NAME)
            text_rect = text.get_rect(center=(center_x, center_y))
            screen.blit(text, text_rect)
    
    def export(self):
        """Creates an SVG polygon element with the space's points"""
        # attrs = {
        #     'points': ' '.join(f"{x},{y}" for x, y in self.points),
        #     'data-id': str(self.id)
        # }
        
        # if self.name:
        #     attrs['data-name'] = self.name
            
        # polygon = ET.Element('polygon', **attrs)
        
        # # Create text element for the name if applicable
        # text = None
        # if self.name:
        #     center_x = sum(p[0] for p in self.points) / len(self.points)
        #     center_y = sum(p[1] for p in self.points) / len(self.points)
            
        #     text_attrs = {
        #         'x': str(center_x),
        #         'y': str(center_y),
        #         'text-anchor': 'middle',
        #         'dy': '.3em',
        #         'style': f'font-size:14px; fill:rgb{Colors.NAME};',
        #         'data-room-id': str(self.id)
        #     }
        #     text = ET.Element('text', **text_attrs)
        #     text.text = self.name
        
        # return polygon, text
        polygon = export_polygon(self.points)
        polygon.set('data-id', str(self.id))
        polygon.set('data-type', 'space')
        if self.name:
            polygon.set('data-name', self.name if self.name else '')

        if self.name:
            text = ET.Element('text', {
                'x': str(self.name_points[0]),
                'y': str(self.name_points[1]),
                'text-anchor': 'middle',
                'dy': '.3em',
                'style': f'font-size:14px; fill:rgb{Colors.NAME};',
                'data-room-id': str(self.id)
            })
            text.text = self.name
            return polygon, text
        else:
            return polygon, None

class Entrance:
    """Entrance element (door)"""
    def __init__(self, line_points, entrance_id=0):
        self.points = line_points  # Start and end points of the line
        self.id = entrance_id
        self.selected = False
        self.color = Colors.ENTRANCE  # Default color for entrance
        self.name = None  # Name of the entrance (if applicable)

        self.midpoint = ((self.points[0][0] + self.points[1][0]) / 2,
                        (self.points[0][1] + self.points[1][1]) / 2)

    def add_name(self, all_spaces):
        """Add name to the entrance based on the spaces it touches"""
        # Find the space that the entrance touches
        midpoint = self.midpoint

        for space in all_spaces:
            if is_point_inside_polygon(midpoint, space.points, tolerance=3):
                if space.name:
                    self.name = space.name
                    return

        # for space in all_spaces:
        #     # Check if the entrance points are inside the space polygon
        #     if is_point_inside_polygon(self.points[0], space.points, tolerance=10):
        #         if space.name:
        #             self.name = space.name
        #             return

        #     if is_point_inside_polygon(self.points[1], space.points, tolerance=10):
        #         if space.name:
        #             self.name = space.name
        #             return
    
    def draw(self, screen, scale, offset):
        # Transform points for drawing
        transformed_points = [transform_point(p, scale, offset) for p in self.points]
        # Draw polygon
        color = Colors.CLICKED if self.selected else Colors.ENTRANCE
        color = color if not self.name else Colors.NAME
        pygame.draw.lines(screen, color, False, transformed_points, 3)
    
    def export(self):
        """Creates an SVG polyline element with the entrance's points"""
        polyline = export_polyline(self.points)
        polyline.set('data-id', str(self.id))
        polyline.set('data-type', 'entrance')

        midpoint = self.midpoint
        
        coordinate = export_point(midpoint)
        coordinate.set('data-id', str(self.id))
        coordinate.set('data-type', 'entrance')
        
        if self.name:
            polyline.set('data-name', self.name if self.name else '')
            coordinate.set('data-name', self.name if self.name else '')
        
        if self.name:
            midpoint = self.midpoint
            text = ET.Element('text', {
                'x': str(midpoint[0]),
                'y': str(midpoint[1]),
                'text-anchor': 'middle',
                'dy': '.3em',
                'style': f'font-size:7px; fill:rgb{Colors.NAME};',
                'data-room-id': str(self.id)
            })
            text.text = self.name
            return coordinate, text
        else:
            return None, None

class Wall:
    """Wall element"""
    def __init__(self, line_points, wall_id=0):
        self.points = line_points  # List of points forming the polyline
        self.id = wall_id
        self.selected = False
        self.color = Colors.WALL  # Default color for wall
        
    def draw(self, screen, scale, offset):
        # Transform points for drawing
        transformed_points = [transform_point(p, scale, offset) for p in self.points]
        # Draw polygon
        color = Colors.CLICKED if self.selected else Colors.WALL
        pygame.draw.lines(screen, color, False, transformed_points, 3)
    
    def export(self):
        """Creates an SVG polyline element with the wall's points"""
        polyline = export_polyline(self.points)
        polyline.set('data-id', str(self.id))
        polyline.set('data-type', 'wall')
        
        return polyline, None

class MidlinePath:
    """Midline path element"""
    def __init__(self, line_points, path_id=0):
        self.points = line_points  # List of points forming the polyline
        self.id = path_id
        self.selected = False
        self.color = Colors.MIDLINE  # Default color for midline path
    
    def draw(self, screen, scale, offset):
        # Transform points for drawing
        transformed_points = [transform_point(p, scale, offset) for p in self.points]
        # Draw polygon
        color = Colors.MIDLINE if not self.selected else Colors.MIDLINE_SELECTED
        pygame.draw.lines(screen, color, False, transformed_points, 3)
    
    def export(self):
        """Creates an SVG polyline element with the midline's points"""
        
        # Check if the midline is selected
        if not self.selected:
            return None, None
        
        polyline = export_polyline(self.points)
        polyline.set('data-id', str(self.id))
        polyline.set('data-type', 'midline')
        
        return polyline, None
    
class GenericPath:
    """Generic path element"""
    def __init__(self, line_points, path_id=0):
        self.points = line_points  # List of points forming the polyline
        self.id = path_id
        self.color = Colors.GENERIC_PATH  # Default color for generic path

    def draw(self, screen, scale, offset):
        # Transform points for drawing
        transformed_points = [transform_point(p, scale, offset) for p in self.points]
        # Draw polygon
        color = Colors.GENERIC_PATH
        pygame.draw.lines(screen, color, False, transformed_points, 3)
    
    def export(self):
        return None, None

class ModeHandler:
    """Handles the current interaction mode"""
    def __init__(self, modes: list[Type['Mode']]):
        self.modes = { mode.__class__: mode for mode in modes } # Dictionary of available modes
        self.current_mode = self.modes[NormalMode] # Default to normal mode

    def handle_key_event(self, key):
        """Check if the key corresponds to any mode"""
        for mode in self.modes.values():
            if key == mode.activate_key:
                self.toggle_mode(mode.__class__)
                return mode
        return None
        
    def get_mode(self, mode_class):
        """Get the current mode"""
        if mode_class in self.modes:
            return self.modes[mode_class]
        return None

    def set_mode(self, mode_class):
        """Set the current interaction mode"""
        if mode_class in self.modes:
            self.current_mode = self.modes[mode_class]

    def toggle_mode(self, mode_class):
        """Toggle between normal mode and the specified mode"""
        if mode_class in self.modes:
            if isinstance(self.current_mode, self.modes[mode_class].__class__):
                print(f"Switching from {self.current_mode.get_mode_name()} to Normal")
                self.set_mode(NormalMode)
            else:
                print(f"Switching to {self.modes[mode_class].get_mode_name()}")
                self.set_mode(mode_class)

    def is_mode(self, mode_class):
        """Check if the current mode is the specified mode"""
        return isinstance(self.current_mode, mode_class)
    
    def get_current_index(self):
        """Get the current index of the mode"""
        return self.current_mode.current_id
    
    def handle_click(self, point, scale, offset, elements):
        """Handle click event based on the current mode"""
        return self.current_mode.handle_click(point, scale, offset, elements)
    
    def delete_selected(self, elements):
        """Delete the selected element"""
        return self.current_mode.delete_selected(elements)

class Mode:
    """Base class for different interaction modes"""
    name = "Normal"  # Default mode name
    color = Colors.SPACE  # Default color for the mode
    activate_key = None  # Key to activate the mode
    element = None  # Default element type

    def __init__(self):
        self.current_id = 1

    def set_mode(self, mode):
        """Set the current mode"""
        pass

    def toggle_mode(self, mode):
        """Toggle between normal mode and the specified mode"""
        pass

    def get_mode_name(self):
        """Get the name of the current mode"""
        return self.name
    
    def get_mode_key(self):
        """Get the key to activate the current mode"""
        return self.activate_key
    
    def is_mode(self: Type['Mode'], mode: Type['Mode']) -> bool:
        """Check if the current mode is the specified mode"""
        return self.name == mode.name

    def increment_id(self):
        """Increment the current ID"""
        self.current_id += 1
        return self.current_id

    def decrement_id(self):
        """Decrement the current ID"""
        self.current_id = max(self.current_id - 1, 1)
        return self.current_id

    def handle_click(self, point, scale, offset, elements):
        """Handle click event based on the current mode"""
        clicked_element = None
        for element in elements:
            if isinstance(element, self.element) and element.is_clicked(point, scale, offset):
                clicked_element = element
                break

        if clicked_element:
            clicked_element.set_selected(not clicked_element.selected)
            return elements
        else:
            # Create a new element if no existing element was clicked
            new_element = self.create_element(point)
            if new_element:
                elements.append(new_element)
                return elements
            
        return elements

    def create_element(self, position):
        """Create a new element based on the current mode"""
        pass

    def delete_selected(self, elements):
        """Delete the selected element"""
        elements = [el for el in elements if not el.selected]
        return elements


class NormalMode(Mode):
    """Normal interaction mode"""
    def __init__(self):
        super().__init__()
        self.element = Space  # Default element type

    def create_element(self, position):
        return None
    
    def delete_selected(self, elements):
        dummy_mode = NamingMode()
        return dummy_mode.delete_selected(elements)


class ElevatorMode(Mode):
    """Elevator interaction mode"""
    def __init__(self):
        super().__init__()
        self.name = "Elevator"
        self.color = Colors.ELEVATOR  # Color for elevator mode
        self.activate_key = KeyBindings.ELEVATOR_MODE  # Key to activate elevator mode
        self.element = Elevator  # Default element type

    def create_element(self, position):
        element = self.element(position, self.current_id)
        self.increment_id()
        return element


class StairsMode(Mode):
    """Stairs interaction mode"""
    def __init__(self):
        super().__init__()
        self.name = "Stairs"
        self.color = Colors.STAIRS  # Color for stairs mode
        self.activate_key = KeyBindings.STAIRS_MODE  # Key to activate stairs mode
        self.element = Stairs  # Default element type

    def create_element(self, position):
        element = self.element(position, self.current_id)
        self.increment_id()
        return element


class NamingMode(Mode):
    """Naming interaction mode"""
    def __init__(self, rooms=[]):
        """Initialize with a list of room names"""
        super().__init__()
        self.name_index = 0
        self.room_names = rooms
        self.name = "Naming"
        self.color = Colors.NAME  # Color for naming mode
        self.activate_key = KeyBindings.NAMING_MODE  # Key to activate naming mode
        self.element = Space  # Default element type

    def increment_id(self):
        self.next_name()

    def decrement_id(self):
        self.previous_name()

    @property
    def current_id(self):
        """Get the current ID"""
        return self.get_current_name()
    
    @current_id.setter
    def current_id(self, value):
        """Set the current ID"""
        pass

    def next_name(self):
        """Move to the next room name"""
        if self.room_names:
            self.name_index = (self.name_index + 1) % len(self.room_names)
        return self.get_current_name()

    def previous_name(self):
        """Move to the previous room name"""
        if self.room_names:
            self.name_index = (self.name_index - 1) % len(self.room_names)
        return self.get_current_name()

    def get_current_name(self):
        """Get the current room name"""
        if self.room_names and self.name_index < len(self.room_names):
            return self.room_names[self.name_index]
        return "Room"

    def set_room_names(self, names):
        """Set the list of room names"""
        self.room_names = names if names else []
        self.name_index = 0

    def handle_click(self, point, scale, offset, elements):
        # TODO: Handle click event for naming mode
        transformed_click = transform_point(point, scale, offset)
        clicked_space = find_innermost_polygon(point, [s.points for s in elements])
        if clicked_space:
            for space in elements:
                if space.points == clicked_space:
                    print(point)
                    space.name_points = point
                    space.name = self.get_current_name()
                    # space.set_selected(False)
                    print(f"Space {space.id + 1} named: {space.name}")

                    self.next_name()

        return elements
    
    def delete_selected(self, elements):
        """Delete the selected element"""
        for el in elements:
            if el.selected and el.name:
                el.name = None
                el.set_selected(False)

        return elements