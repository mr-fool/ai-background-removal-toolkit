import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
from rembg import remove
import threading
from tkinterdnd2 import DND_FILES, TkinterDnD

class BackgroundRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Background Remover")
        self.root.geometry("800x600")
        self.root.configure(padx=20, pady=20)
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.preview_img = None
        self.processed_img = None
        
        # Create the UI
        self.create_widgets()
        
        # Setup initial drag and drop for the entire window
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_handler)
        
    def create_widgets(self):
        # Frame for input section
        input_frame = ttk.LabelFrame(self.root, text="Input Image")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Input file selection
        ttk.Label(input_frame, text="Select Image:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(input_frame, text="Enable Drop Zone", command=self.setup_drag_drop).grid(row=0, column=3, padx=5, pady=5)
        
        # Frame for output section
        output_frame = ttk.LabelFrame(self.root, text="Output Image")
        output_frame.pack(fill="x", padx=10, pady=10)
        
        # Output file selection
        ttk.Label(output_frame, text="Save To:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).grid(row=0, column=2, padx=5, pady=5)
        
        # Preview area
        preview_frame = ttk.LabelFrame(self.root, text="Preview")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a canvas for the preview
        self.canvas = tk.Canvas(preview_frame, bg="lightgray")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a message to display when no image is loaded
        self.canvas.create_text(400, 200, text="No image loaded", fill="black", font=("Arial", 16))
        
        # Buttons frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(button_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(side="left", padx=10, pady=10)
        
        # Process button
        self.process_button = ttk.Button(button_frame, text="Remove Background", command=self.process_image)
        self.process_button.pack(side="right", padx=10, pady=10)
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select an image",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*"))
        )
        if filename:
            self.input_path.set(filename)
            self.update_preview(filename)
            
            # Auto-generate output path
            base, ext = os.path.splitext(filename)
            output_filename = f"{base}_no_bg.png"
            self.output_path.set(output_filename)
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save processed image",
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"), ("All files", "*.*"))
        )
        if filename:
            self.output_path.set(filename)
    
    def update_preview(self, image_path):
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Resize for preview (maintain aspect ratio)
            width, height = img.size
            max_size = 400
            ratio = min(max_size/width, max_size/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.preview_img = ImageTk.PhotoImage(img)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(400, 200, anchor="center", image=self.preview_img)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def process_image(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output files")
            return
        
        # Start progress bar
        self.progress.start()
        self.process_button.configure(state="disabled")
        
        # Process in a separate thread to prevent UI freezing
        threading.Thread(target=self._process_thread, args=(input_path, output_path)).start()
    
    def _process_thread(self, input_path, output_path):
        try:
            # Open the image
            inp = Image.open(input_path)
            
            # Remove background
            output = remove(inp)
            
            # Save the result
            output.save(output_path)
            
            # Update UI in the main thread
            self.root.after(0, self._update_after_processing, output_path)
            
        except Exception as e:
            # Show error in the main thread
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process image: {str(e)}"))
            self.root.after(0, self._reset_ui)
    
    def _update_after_processing(self, output_path):
        # Stop progress
        self.progress.stop()
        self.process_button.configure(state="normal")
        
        # Display the processed image
        try:
            self.update_preview(output_path)
            messagebox.showinfo("Success", f"Background removed successfully!\nSaved to: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display processed image: {str(e)}")
    
    def _reset_ui(self):
        self.progress.stop()
        self.process_button.configure(state="normal")
        
    def drop_handler(self, event):
        # Extract the file path from the event
        file_path = event.data
        
        # Clean up the file path (tkinterdnd2 adds curly braces and potentially quotes)
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        
        # On Windows, the path might have additional quotes
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
            
        # Check if it's an image file
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        if file_path.lower().endswith(valid_extensions):
            self.input_path.set(file_path)
            self.update_preview(file_path)
            
            # Auto-generate output path
            base, ext = os.path.splitext(file_path)
            output_filename = f"{base}_no_bg.png"
            self.output_path.set(output_filename)
        else:
            messagebox.showerror("Invalid File", "Please drop an image file (jpg, jpeg, png, bmp, gif)")
            
        # Reset canvas appearance if needed
        if self.canvas.cget("bg") == "#e0f7fa":  # If it was in "drop zone" mode
            self.canvas.config(bg="lightgray")
            # If no image is loaded, show the default message
            if not self.preview_img:
                self.canvas.delete("all")
                self.canvas.create_text(400, 200, text="No image loaded", fill="black", font=("Arial", 16))
    
    def setup_drag_drop(self):
        # Register the canvas as a drop target
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.drop_handler)
        
        # Change canvas appearance to indicate drop zone
        self.canvas.delete("all")
        self.canvas.config(bg="#e0f7fa")  # Light blue background to indicate drop zone
        self.canvas.create_text(400, 180, text="Drop Image Here", fill="#0277bd", font=("Arial", 20, "bold"))
        self.canvas.create_text(400, 220, text="Drag and drop an image file from your computer", 
                               fill="#0277bd", font=("Arial", 12))
        
        # Add icon or visual indicator for drop zone (a simple rectangle in this case)
        self.canvas.create_rectangle(250, 100, 550, 300, outline="#0277bd", width=2, dash=(7, 3))
        
if __name__ == "__main__":
    root = TkinterDnD.Tk()  # Use TkinterDnD instead of standard Tk
    app = BackgroundRemoverApp(root)
    root.mainloop()