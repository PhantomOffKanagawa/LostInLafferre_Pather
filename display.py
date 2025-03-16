import pygame
import os
import json
from shapely import Polygon
from geometry_utils import transform_shapes, inverse_transform_point, zoom_at, is_point_near_line
from geometry_utils import find_innermost_polygon, is_point_inside_polygon, shapely_to_pygame
from geometry_utils import find_midline_path, nearest_point_on_line, transform_point
from svg_parser import parse_svg, export_svg
from classes import MapElement, Elevator, Stairs, Space, Entrance, Wall, MidlinePath, GenericPath, Mode
from classes import NormalMode, ElevatorMode, StairsMode, NamingMode, ModeHandler
from values import Colors, Paths, KeyBindings, Constants

class MapWindow:
    """Main map display and interaction window"""
    def __init__(self, file_path, map_name, on_close):
        pygame.init()
        self.file_path = file_path
        self.map_name = map_name
        self.on_close = on_close

        self.element_classes = [ Space, Wall, Entrance, Elevator, Stairs, MidlinePath ]
        self.element_stores = {cls.__name__: [] for cls in self.element_classes}

        # Parse SVG file
        svg_outputs = parse_svg(file_path)
        
        self.width = svg_outputs['screen_width']
        self.height = svg_outputs['screen_height']

        for cls in self.element_classes:
            self.element_stores[cls.__name__] = svg_outputs.get(cls.__name__, [])

        # Initialize mode handler
        self.mode_handler = ModeHandler([NormalMode(), ElevatorMode(), StairsMode(), NamingMode()])

        # Create a new pygame window
        self.window_id = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE | pygame.HWSURFACE)
        pygame.display.set_caption(f"Pather - {map_name}")
        
        # View control variables
        self.scale = 1.0
        self.offset = [0, 0]
        self.dragging = False
        self.drag_start = (0, 0)
        
        # Load room names from JSON
        self.load_room_names()
        
        # Load saved settings if they exist
        self.load_settings()
        
        # Start the rendering loop
        self.running = True
        self.run()
    
    def load_room_names(self):
        """Load room names from JSON file and set them in the mode manager"""
        try:
            filename = Paths.ROOM_NAMES_FILE + self.map_name + '.json'
            with open(filename, 'r') as file:
                data = json.load(file)
                room_names = list(data.keys())
                self.mode_handler.get_mode(NamingMode).set_room_names(room_names)
                print(f"Loaded {len(room_names)} room names")
        except FileNotFoundError:
            print("No room names file found.")
            self.mode_handler.get_mode(NamingMode).set_room_names([])
            # self.save_room_names()
        except json.JSONDecodeError:
            print("Error parsing room names file.")
            self.mode_handler.get_mode(NamingMode).set_room_names([])
            
    # def save_room_names(self):
    #     """Save room names to JSON file"""
    #     with open(Paths.ROOM_NAMES_FILE, 'w') as file:
    #         json.dump({"names": self.mode.room_names}, file)
    
    def run(self):
        """Main loop for the map window"""
        # TODO: Only run loop when updates are needed
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        # Notify the main application when this window closes
        self.on_close(self)
    
    def handle_events(self):
        """Handle pygame events for this window"""
        mouse_pos = pygame.mouse.get_pos()
        transformed_mouse_pos = inverse_transform_point(mouse_pos, self.scale, self.offset)
        
        # Handle hover effect if not in special modes
        # TODO: Move handle hover to classes?
        if self.mode_handler.is_mode(NormalMode):
            self.handle_hover(transformed_mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
            
            elif event.type == pygame.KEYDOWN:
                self.handle_keyboard_event(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_button_down(event, transformed_mouse_pos, mouse_pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:  # Middle click
                    self.dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx, dy = event.rel
                    self.offset[0] += dx
                    self.offset[1] += dy
            
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.window_id = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE | pygame.HWSURFACE)
    
    def handle_keyboard_event(self, event):
        """Handle keyboard events"""

        if event.key == KeyBindings.ID_UP:  # Increment ID
            self.mode_handler.current_mode.increment_id()

        elif event.key == KeyBindings.ID_DOWN:  # Decrement ID
            self.mode_handler.current_mode.decrement_id()

        elif event.key == KeyBindings.MIDLINE:  # Calculate midline paths for selected spaces
            self.calculate_midline_paths()
        
        elif event.key == KeyBindings.ALL_MIDLINES:  # Calculate all midline paths
            self.calculate_all_midline_paths()
        
        elif event.key == KeyBindings.EXPORT:  # Export SVG
            self.export_svg()
        
        elif event.key == KeyBindings.SAVE:  # Save settings
            self.save_settings()
        
        elif event.key == KeyBindings.LOAD:  # Load settings
            self.load_settings()

        elif event.key == KeyBindings.DELETE:  # Delete selected item
            self.delete_selected_items()
        
        elif event.key == KeyBindings.ESCAPE:  # Close window with ESC key
            self.close()
        
        else:
            # Check if mode activation
            self.mode_handler.handle_key_event(event.key)
    
    def handle_mouse_button_down(self, event, transformed_mouse_pos, screen_mouse_pos):
        """Handle mouse button down events"""
        if event.button == 1:  # Left click
            if self.mode_handler.is_mode(NormalMode):
                self.handle_normal_click(transformed_mouse_pos)
            else:
                self.handle_mode_click(screen_mouse_pos)
        
        elif event.button == 2:  # Middle click press
            self.dragging = True
            self.drag_start = pygame.mouse.get_pos()
        
        elif event.button == 4:  # Scroll up - zoom in
            zoom_factor = 1.1
            self.scale, self.offset = zoom_at(self.scale, self.offset, pygame.mouse.get_pos(), zoom_factor)
        
        elif event.button == 5:  # Scroll down - zoom out
            zoom_factor = 0.9
            self.scale, self.offset = zoom_at(self.scale, self.offset, pygame.mouse.get_pos(), zoom_factor)
    
    def handle_hover(self, mouse_pos):
        """Handle hover effects for spaces and other elements"""
        # Reset colors first
        for space in self.element_stores['Space']:
            if not space.selected:
                space.color = Colors.SPACE
        
        # Find hovered space
        hovered_space = find_innermost_polygon(mouse_pos, [s.points for s in self.element_stores['Space']])
        if hovered_space:
            for space in self.element_stores['Space']:
                if space.points == hovered_space and not space.selected:
                    space.color = Colors.HIGHLIGHT
    
    def handle_normal_click(self, mouse_pos):
        """Handle clicks in normal mode (select spaces)"""
        clicked_space = find_innermost_polygon(mouse_pos, [s.points for s in self.element_stores['Space']])
        if clicked_space:
            for space in self.element_stores['Space']:
                if space.points == clicked_space:
                    space.selected = not space.selected
                    # space.update_color()
                    print(f"Space {space.id + 1}: {'selected' if space.selected else 'deselected'}")
                    break

    def handle_mode_click(self, mouse_pos):
        """Handle clicks in special modes (elevator, stairs, naming)"""
        current_mode_element = self.mode_handler.current_mode.element.__name__
        elements = self.element_stores[current_mode_element]
        self.element_stores[current_mode_element] = self.mode_handler.handle_click(mouse_pos, self.scale, self.offset, elements)
    
    def delete_selected_items(self):
        """Delete selected elevators or stairs"""
        current_mode_element = self.mode_handler.current_mode.element.__name__
        elements = self.element_stores[current_mode_element]
        elements = [el for el in elements if not el.selected]
        self.element_stores[current_mode_element] = elements
    
    def calculate_midline_paths(self):
        """Calculate midline paths for selected spaces"""
        # Get list of selected spaces and their indices
        selected_spaces = [(i, space) for i, space in enumerate(self.element_stores['Space']) if space.selected]
        named_space_indices = [i for i, space in enumerate(self.element_stores['Space']) if space.name]
        
        self.element_stores['MidlinePath'] = []
        
        for i, space in selected_spaces:
            # Skip named spaces
            if i in named_space_indices:
                continue
                
            print(f"Calculating midline for space {i + 1}")
            midline_path = find_midline_path(polygon=space.points)
            
            # Handle different return types from find_midline_path
            if isinstance(midline_path, list) and all(isinstance(item, list) for item in midline_path):
                for path in midline_path:
                    self.element_stores['MidlinePath'].append(MidlinePath(path, len(self.element_stores['MidlinePath'])))
            else:
                self.element_stores['MidlinePath'].append(MidlinePath(midline_path, len(self.element_stores['MidlinePath'])))
            
            # Add paths from doors to the nearest point on the midline
            for entrance in self.element_stores['Entrance']:
                midpoint = ((entrance.points[0][0] + entrance.points[1][0]) / 2, 
                           (entrance.points[0][1] + entrance.points[1][1]) / 2)
                if is_point_inside_polygon(midpoint, space.points, tolerance=5):
                    nearest_point = nearest_point_on_line(midpoint, midline_path)
                    self.element_stores['MidlinePath'].append(MidlinePath([midpoint, nearest_point], 
                                                        len(self.element_stores['MidlinePath'])))
            
            # Add paths from elevators to the nearest point on the midline
            for elevator in self.element_stores['Elevator']:
                if is_point_inside_polygon(elevator.position, space.points, tolerance=5):
                    nearest_point = nearest_point_on_line(elevator.position, midline_path)
                    self.element_stores['MidlinePath'].append(MidlinePath([elevator.position, nearest_point], 
                                                        len(self.element_stores['MidlinePath'])))
            
            # Add paths from stairs to the nearest point on the midline
            for stair in self.element_stores['Stairs']:
                if is_point_inside_polygon(stair.position, space.points, tolerance=5):
                    nearest_point = nearest_point_on_line(stair.position, midline_path)
                    self.element_stores['MidlinePath'].append(MidlinePath([stair.position, nearest_point], 
                                                        len(self.element_stores['MidlinePath'])))
        
        print(f"Generated {len(self.element_stores['MidlinePath'])} midline path segments")
    
    def calculate_all_midline_paths(self):
        """Calculate midline paths for all spaces except named ones"""
        # Save the current selection state
        previous_selection = [space.selected for space in self.element_stores['Space']]
        
        # Select all spaces except named ones
        named_indices = [i for i, space in enumerate(self.element_stores['Space']) if space.name]
        for i, space in enumerate(self.element_stores['Space']):
            space.selected = i not in named_indices
        
        # Calculate midlines
        self.calculate_midline_paths()
        
        # Restore previous selection
        for i, selected in enumerate(previous_selection):
            if i < len(self.element_stores['Space']):
                self.element_stores['Space'][i].selected = selected
                # self.element_stores['Space'][i].update_color()
    
    def export_svg(self, debug=False):
        """Export the current state to an SVG file"""
        output_path = f"{Paths.SETTINGS_DIR}{self.map_name}_{'debug' if debug else 'output'}.svg"
        
        export_svg(
            output_path, 
            self.element_stores
        )
    
    def save_settings(self):
        """Save settings to a JSON file"""
        file_path = f"{Paths.SETTINGS_DIR}{self.map_name}_settings.json"
        
        # Create a dictionary of settings to save
        settings = {
            "elevators": [{"position": elevator.position, 
                          "id": elevator.id, 
                          "selected": elevator.selected} 
                         for elevator in self.element_stores['Elevator']],
            
            "stairs": [{"position": stairs.position, 
                       "id": stairs.id, 
                       "selected": stairs.selected} 
                      for stairs in self.element_stores['Stairs']],
            
            "spaces": [{"id": space.id, 
                       "selected": space.selected, 
                       "name": space.name} 
                      for space in self.element_stores['Space']]
        }
        
        with open(file_path, 'w') as file:
            json.dump(settings, file)
        
        print(f"Settings saved to {file_path}")
    
    def load_settings(self):
        """Load settings from a JSON file"""
        file_path = f"{Paths.SETTINGS_DIR}{self.map_name}_settings.json"
        
        try:
            with open(file_path, 'r') as file:
                settings = json.load(file)
                
                # Load elevators
                elevators_data = settings.get("elevators", [])
                if elevators_data:
                    self.element_stores['Elevator'] = []
                    for e_data in elevators_data:
                        elevator = Elevator(
                            position=tuple(e_data["position"]), 
                            elevator_id=e_data.get("id", 1)
                        )
                        elevator.selected = e_data.get("selected", False)
                        self.element_stores['Elevator'].append(elevator)
                
                # Load stairs
                stairs_data = settings.get("stairs", [])
                if stairs_data:
                    self.element_stores['Stairs'] = []
                    for s_data in stairs_data:
                        stair = Stairs(
                            position=tuple(s_data["position"]), 
                            stairs_id=s_data.get("id", 1)
                        )
                        stair.selected = s_data.get("selected", False)
                        self.element_stores['Stairs'].append(stair)
                
                # Load spaces (selection and names)
                spaces_data = settings.get("spaces", [])
                if spaces_data:
                    for s_data in spaces_data:
                        space_id = s_data.get("id", 0)
                        if 0 <= space_id < len(self.element_stores['Space']):
                            self.element_stores['Space'][space_id].selected = s_data.get("selected", False)
                            self.element_stores['Space'][space_id].name = s_data.get("name")
                            # self.element_stores['Space'][space_id].update_color()
                
                print(f"Settings loaded from {file_path}")
        except FileNotFoundError:
            print(f"No saved file found at {file_path}")
        except json.JSONDecodeError:
            print(f"Error parsing settings file at {file_path}")
    
    def close(self):
        """Properly close the window and notify the main application"""
        print(f"Closing window: {self.map_name}")
        self.running = False
    
    def draw(self):
        """Draw all elements to the screen"""
        # Clear screen
        self.window_id.fill(Colors.BACKGROUND)
        
        # Draw elements in the order of their classes
        # TODO: Implement a more efficient way to draw elements (only when changed)
        # TODO: Implement better draw ordering
        for key, element in self.element_stores.items():
            if not element or element == []:
                continue
            
            for el in element:
                el.draw(self.window_id, self.scale, self.offset)

        # Draw mode indicator
        self.draw_mode_indicator()
    
    def draw_mode_indicator(self):
        """Draw current mode indicator"""
        mode_text = ""
        text_color = Colors.SPACE
        
        if not self.mode_handler.is_mode(NormalMode):            
            mode_text = self.mode_handler.current_mode.name
            mode_text += " (ID: " + str(self.mode_handler.current_mode.current_id) + ")"
            text_color = self.mode_handler.current_mode.color
        
        if mode_text:
            font = pygame.font.SysFont(Constants.DEFAULT_FONT, 20)
            text = font.render(mode_text, True, text_color)
            self.window_id.blit(text, (10, 10))