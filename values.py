import pygame

class Colors:
    """Color constants used throughout the application"""
    ENTRANCE = (0, 100, 255)  # Blue
    SPACE = (0, 100, 100)  # Green
    WALL = (200, 200, 200)  # Gray
    HIGHLIGHT = (50, 50, 50)  # Darker
    CLICKED = (0, 150, 150)  # Orange
    MIDLINE = (255, 0, 0)  # Red
    ELEVATOR = (255, 0, 255)  # Magenta
    ELEVATOR_SELECTED = (255, 150, 255)  # Light Magenta
    STAIRS = (200, 200, 0)  # Yellow
    STAIRS_SELECTED = (255, 255, 0)  # Light Yellow
    SHAPE = (0, 0, 0)  # Black
    NAME = (0, 0, 200)  # Dark Blue for room names
    TEXT = (255, 255, 255)  # White for text
    BACKGROUND = (255, 255, 255)  # White background
    GENERIC_PATH = (0, 0, 0)  # Black for generic paths

class Paths:
    """Default path constants"""
    INPUT = "./ver-0.0.4-svgs/three.svg"  # Default input SVG file path
    OUTPUT = "./output/output.svg"  # Default output SVG file path
    SETTINGS_DIR = "./output/"  # Directory for settings files
    ROOM_NAMES_FILE = "./room_names/"  # Room names file path

class KeyBindings:
    """Keyboard shortcut bindings"""
    MIDLINE = pygame.K_m  # Calculate midline paths for selected spaces
    ALL_MIDLINES = pygame.K_a  # Calculate all midline paths
    EXPORT = pygame.K_e  # Export SVG
    EXPORT_DEBUG = pygame.K_r  # Export SVG with debug info
    SAVE = pygame.K_s  # Save selected spaces
    LOAD = pygame.K_l  # Load selected spaces
    STAIRS_MODE = pygame.K_c  # Toggle stairs mode
    ELEVATOR_MODE = pygame.K_v  # Toggle elevator mode
    ID_UP = pygame.K_UP  # Increment ID
    ID_DOWN = pygame.K_DOWN  # Decrement ID
    DELETE = pygame.K_DELETE  # Delete selected item
    NAMING_MODE = pygame.K_n  # Toggle room naming mode
    ESCAPE = pygame.K_ESCAPE  # Close window

class Constants:
    """Misc constants used in the application"""
    MAX_ELEVATOR_ID = 99  # Maximum elevator ID
    MAX_STAIRS_ID = 99  # Maximum stairs ID
    DEFAULT_FONT = 'Arial'  # Default font for text
    DEFAULT_RADIUS = 8  # Default radius for shapes
    MODE_NORMAL = 0  # Normal mode (no special mode)
    MODE_ELEVATOR = 1  # Elevator mode
    MODE_STAIRS = 2  # Stairs mode
    MODE_NAMING = 3  # Room naming mode