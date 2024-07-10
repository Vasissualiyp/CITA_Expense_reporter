import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

class ImageViewer:
    def __init__(self, master, image_path):
        self.master = master
        self.master.title("Image Viewer")

        # Load the image
        self.original_image = Image.open(image_path)
        self.working_image = self.original_image.copy()
        self.image = ImageTk.PhotoImage(self.working_image)

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
        self.rectangles = []

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        # Create buttons
        self.create_buttons()

        # Create zoom bar
        self.create_zoom_bar()

    def create_buttons(self):
        button_frame = ttk.Frame(self.master)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        undo_button = ttk.Button(button_frame, text="Undo", command=self.undo_last_rectangle)
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
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            x1, y1 = min(self.start_x, x), min(self.start_y, y)
            x2, y2 = max(self.start_x, x), max(self.start_y, y)
            self.add_black_rectangle(x1, y1, x2, y2)
        self.start_x = None
        self.start_y = None
        self.rect = None

    def add_black_rectangle(self, x1, y1, x2, y2):
        # Convert canvas coordinates to image coordinates
        x1, y1 = self.canvas_to_image(x1, y1)
        x2, y2 = self.canvas_to_image(x2, y2)
        
        draw = ImageDraw.Draw(self.working_image)
        draw.rectangle([x1, y1, x2, y2], fill="black")
        self.rectangles.append((x1, y1, x2, y2))
        self.update_image()

    def undo_last_rectangle(self):
        if self.rectangles:
            self.rectangles.pop()
            self.working_image = self.original_image.copy()
            draw = ImageDraw.Draw(self.working_image)
            for rect in self.rectangles:
                draw.rectangle(rect, fill="black")
            self.update_image()

    def on_mousewheel(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))
        self.zoom_bar.set(self.zoom_factor)
        self.update_image(x, y)

    def on_ctrl_mousewheel(self, event):
        if event.state & 0x4:  # Check if Ctrl key is pressed
            self.on_mousewheel(event)

    def on_zoom(self, value):
        current_x = self.canvas.canvasx(self.canvas.winfo_width() / 2)
        current_y = self.canvas.canvasy(self.canvas.winfo_height() / 2)
        self.zoom_factor = float(value)
        self.update_image(current_x, current_y)

    def update_image(self, focus_x=None, focus_y=None):
        new_width = int(self.working_image.width * self.zoom_factor)
        new_height = int(self.working_image.height * self.zoom_factor)
        resized_image = self.working_image.resize((new_width, new_height), Image.LANCZOS)
        self.image = ImageTk.PhotoImage(resized_image)
        
        if focus_x is None or focus_y is None:
            self.canvas.coords(self.image_on_canvas, 0, 0)
        else:
            # Calculate new position to keep the focus point stationary
            current_x, current_y = self.canvas.coords(self.image_on_canvas)
            delta_x = (focus_x - current_x) * (1 - self.zoom_factor / self.canvas.get_zoom_factor())
            delta_y = (focus_y - current_y) * (1 - self.zoom_factor / self.canvas.get_zoom_factor())
            new_x = current_x - delta_x
            new_y = current_y - delta_y
            self.canvas.coords(self.image_on_canvas, new_x, new_y)
        
        self.canvas.itemconfig(self.image_on_canvas, image=self.image)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def canvas_to_image(self, x, y):
        # Convert canvas coordinates to image coordinates
        canvas_x, canvas_y = self.canvas.coords(self.image_on_canvas)
        image_x = int((x - canvas_x) / self.zoom_factor)
        image_y = int((y - canvas_y) / self.zoom_factor)
        return image_x, image_y

    def get_zoom_factor(self):
        return self.zoom_factor

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root, "05-31/creditcard.jpg")
    root.mainloop()
