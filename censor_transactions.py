import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ImageViewer:
    def __init__(self, master, image_path):
        self.master = master
        self.master.title("Image Viewer")

        # Load the image
        self.original_image = Image.open(image_path)
        self.image = ImageTk.PhotoImage(self.original_image)

        # Create canvas
        self.canvas = tk.Canvas(self.master, width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Display image on canvas
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)

        # Zoom variables
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Rectangle variables
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        # Create buttons
        self.create_buttons()

        # Create zoom bar
        self.create_zoom_bar()

    def create_buttons(self):
        button_frame = ttk.Frame(self.master)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        save_button = ttk.Button(button_frame, text="Save")
        save_button.pack(side=tk.LEFT, padx=5, pady=5)

        undo_button = ttk.Button(button_frame, text="Undo")
        undo_button.pack(side=tk.LEFT, padx=5, pady=5)

        exit_button = ttk.Button(button_frame, text="Exit", command=self.master.quit)
        exit_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def create_zoom_bar(self):
        zoom_frame = ttk.Frame(self.master)
        zoom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
        self.zoom_bar = ttk.Scale(zoom_frame, from_=self.min_zoom, to=self.max_zoom,
                                  orient=tk.HORIZONTAL, value=1.0, command=self.on_zoom)
        self.zoom_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def on_drag(self, event):
        if self.start_x and self.start_y:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, x, y, outline="red")

    def on_release(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
        self.start_x = None
        self.start_y = None
        self.rect = None

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))
        self.zoom_bar.set(self.zoom_factor)
        self.update_image()

    def on_zoom(self, value):
        self.zoom_factor = float(value)
        self.update_image()

    def update_image(self):
        new_width = int(self.original_image.width * self.zoom_factor)
        new_height = int(self.original_image.height * self.zoom_factor)
        resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.image = ImageTk.PhotoImage(resized_image)
        self.canvas.itemconfig(self.image_on_canvas, image=self.image)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root, "05-31/creditcard.jpg")
    root.mainloop()
