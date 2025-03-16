import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import traceback
from display import MapWindow
from values import Paths

class MainApplication:
    """Main application for Pather SVG Annotation Tool"""
    def __init__(self, root):
        self.root = root
        self.root.title("Pather - SVG Map Annotation Tool")
        self.root.geometry("500x300")
        
        self.current_window = None
        
        self.create_menu()
        
        welcome_label = tk.Label(root, text="Welcome to Pather\nSVG Map Annotation Tool", font=("Arial", 16))
        welcome_label.pack(pady=20)
        
        open_button = tk.Button(root, text="Open SVG Map", command=self.open_svg, height=2, width=20)
        open_button.pack(pady=10)
        
        self.create_recent_files_section()
        
        os.makedirs(os.path.dirname(Paths.OUTPUT), exist_ok=True)
        
    def create_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open SVG", command=self.open_svg)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        helpmenu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        self.root.config(menu=menubar)
    
    def create_recent_files_section(self):
        """Create a section for recent files"""
        recent_frame = tk.Frame(self.root)
        recent_frame.pack(pady=10, fill=tk.X)
        
        recent_label = tk.Label(recent_frame, text="Recent Files:", font=("Arial", 10, "bold"))
        recent_label.pack(anchor="w", padx=20)
        
        no_files_label = tk.Label(recent_frame, text="No recent files", font=("Arial", 9))
        no_files_label.pack(anchor="w", padx=30)
        
    def open_svg(self):
        """Open an SVG file and create a MapWindow for editing"""
        if self.current_window and self.current_window.running:
            self.current_window.close()
            self.current_window = None

        file_path = filedialog.askopenfilename(
            initialdir="./",
            title="Select SVG file",
            filetypes=(("SVG files", "*.svg"), ("all files", "*.*"))
        )
        
        if file_path:
            try:
                map_name = os.path.splitext(os.path.basename(file_path))[0]
                self.current_window = MapWindow(file_path, map_name, on_close=self.on_window_close)
            except Exception as e:
                line_number = traceback.extract_tb(e.__traceback__)[-1].lineno
                messagebox.showerror("Error", f"Failed to open SVG: {e} (Line {line_number})")
                print(f"Error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
    
    def on_window_close(self, window):
        """Handle window close event"""
        if window == self.current_window:
            self.current_window = None
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Pather - SVG Map Annotation Tool
        
        A tool for annotating SVG maps of buildings with paths for navigation.
        
        Released under GNU GPL v3
        """
        messagebox.showinfo("About Pather", about_text)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """
        Keyboard Shortcuts:
        
        M - Calculate midline paths for selected spaces
        A - Calculate all midline paths
        E - Export SVG
        R - Export SVG with debug info
        S - Save selections
        L - Load selections
        N - Toggle room naming mode
        V - Toggle elevator mode
        C - Toggle stairs mode
        Up/Down Arrows - Navigate IDs/names
        Delete - Delete selected item
        Escape - Close window
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

def main():
    """Main entry point for the application"""
    pygame.init()
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
    pygame.quit()

if __name__ == "__main__":
    main()
