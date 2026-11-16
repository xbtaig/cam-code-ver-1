import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from scanner_app.core.camera import Camera
from scanner_app.core.scanner import compare_images
from scanner_app.core.storage import InspectionStorage


class InspectionApp:
    PREVIEW_SIZE = (400, 300)

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Visual Parts Inspector")
        self.root.geometry("1280x670")
        self.root.minsize(900, 600)

        self.storage = InspectionStorage()
        self.camera = None
        self.master_image = None
        self.last_result_image = None
        self._photos = {}
        self.status_text = tk.StringVar(value="Connect a camera and capture or load a master sample.")
        self.result_text = tk.StringVar(value="WAITING")
        self.camera_index = tk.StringVar(value="0")
        self.sensitivity = tk.IntVar(value=35)
        self.min_area = tk.IntVar(value=150)

        self._build_ui()
        try:
            self.master_image = self.storage.load_master()
        except OSError as error:
            self.status_text.set(str(error))
        if self.master_image is not None:
            self.status_text.set("Saved master sample loaded.")
            self._show_image("master", self.master_image)
        self._connect_camera()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(30, self._refresh_live_view)

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="VISUAL PARTS INSPECTOR", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.result_label = tk.Label(
            header,
            textvariable=self.result_text,
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#64748b",
            padx=24,
            pady=6,
        )
        self.result_label.grid(row=0, column=2, sticky="e")

        previews = ttk.Frame(self.root, padding=(12, 4))
        previews.grid(row=1, column=0, sticky="nsew")
        for column in range(3):
            previews.columnconfigure(column, weight=1)
        previews.rowconfigure(1, weight=1)

        panels = (
            ("master", "Master sample"),
            ("live", "Live camera"),
            ("result", "Inspection result (red = changed)"),
        )
        for column, (key, title) in enumerate(panels):
            ttk.Label(previews, text=title, font=("Segoe UI", 11, "bold")).grid(
                row=0, column=column, pady=(4, 8)
            )
            image_label = tk.Label(
                previews,
                text="No image",
                bg="#111827",
                fg="#d1d5db",
                width=48,
                height=18,
            )
            image_label.grid(row=1, column=column, padx=6, sticky="nsew")
            setattr(self, key + "_label", image_label)

        controls = ttk.LabelFrame(self.root, text="Controls", padding=12)
        controls.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 4))
        ttk.Label(controls, text="Camera index").grid(row=0, column=0, padx=(0, 5))
        ttk.Combobox(
            controls,
            values=tuple(str(index) for index in range(11)),
            width=5,
            state="readonly",
            textvariable=self.camera_index,
        ).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(controls, text="Connect / restart", command=self._connect_camera).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(controls, text="Capture master", command=self._capture_master).grid(
            row=0, column=3, padx=4
        )
        ttk.Button(controls, text="Save live photo", command=self._save_live_photo).grid(
            row=0, column=4, padx=4
        )
        ttk.Button(controls, text="Load master image", command=self._load_master_file).grid(
            row=0, column=5, padx=4
        )
        ttk.Button(controls, text="Inspect part", command=self._inspect).grid(
            row=0, column=6, padx=4
        )
        ttk.Label(controls, text="Sensitivity").grid(row=1, column=0, padx=(0, 4), pady=(10, 0))
        ttk.Scale(
            controls,
            from_=10,
            to=100,
            variable=self.sensitivity,
            orient="horizontal",
            length=180,
        ).grid(row=1, column=1, padx=4, pady=(10, 0))
        ttk.Label(controls, text="Min area (px)").grid(
            row=1, column=2, padx=(18, 4), pady=(10, 0)
        )
        ttk.Scale(
            controls,
            from_=20,
            to=2000,
            variable=self.min_area,
            orient="horizontal",
            length=180,
        ).grid(row=1, column=3, padx=4, pady=(10, 0))

        footer = ttk.Frame(self.root, padding=(14, 8, 14, 12))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_text, wraplength=950).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(footer, text="Saved in the project data folder", foreground="#64748b").grid(
            row=0, column=1, sticky="e"
        )

    def _connect_camera(self):
        if self.camera is not None:
            self.camera.close()
            self.camera = None
        try:
            self.camera = Camera(int(self.camera_index.get()))
            self.status_text.set(
                "Camera connected. Keep the camera and part position fixed."
            )
        except (RuntimeError, ValueError) as error:
            self.status_text.set(str(error))

    def _save_live_photo(self):
        frame = self.camera.get_frame() if self.camera else None
        if frame is None:
            messagebox.showwarning(
                "No camera frame", "Connect a working webcam before saving a photo."
            )
            return
        try:
            image_path = self.storage.save_capture(frame)
            self.status_text.set(
                "Live photo saved to {}.".format(
                    image_path.relative_to(self.storage.data_dir.parent)
                )
            )
        except OSError as error:
            messagebox.showerror("Could not save photo", str(error))

    def _capture_master(self):
        frame = self.camera.get_frame() if self.camera else None
        if frame is None:
            messagebox.showwarning("No camera frame", "Connect a working webcam before capturing.")
            return
        try:
            self.storage.save_master(frame)
            self.master_image = frame
            self.last_result_image = None
            self._show_image("master", frame)
            self._show_image("result", None)
            self._set_result("WAITING")
            self.status_text.set("Master sample saved to data\\samples\\master.jpg.")
        except OSError as error:
            messagebox.showerror("Could not save master", str(error))

    def _load_master_file(self):
        filename = filedialog.askopenfilename(
            title="Select a master sample image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")],
        )
        if not filename:
            return
        image = cv2.imread(filename)
        if image is None:
            messagebox.showerror("Invalid image", "The selected file could not be opened as an image.")
            return
        try:
            self.storage.save_master(image)
            self.master_image = image
            self._show_image("master", image)
            self._show_image("result", None)
            self._set_result("WAITING")
            self.status_text.set("Selected image saved as the current master sample.")
        except OSError as error:
            messagebox.showerror("Could not save master", str(error))

    def _inspect(self):
        if self.master_image is None:
            messagebox.showwarning("Master sample required", "Capture or load a master sample first.")
            return
        frame = self.camera.get_frame() if self.camera else None
        if frame is None:
            messagebox.showwarning("No camera frame", "Connect a working webcam before inspecting.")
            return
        try:
            result = compare_images(
                self.master_image,
                frame,
                sensitivity=self.sensitivity.get(),
                min_area=self.min_area.get(),
            )
            image_path = self.storage.save_inspection(result)
            self.last_result_image = result.annotated_frame
            self._show_image("result", result.annotated_frame)
            self._set_result(result.status)
            self.status_text.set(
                "{}: {} changed region(s), {} px total. Saved {}.".format(
                    result.status,
                    result.difference_count,
                    result.changed_area,
                    image_path.relative_to(self.storage.data_dir.parent),
                )
            )
        except (OSError, ValueError, cv2.error) as error:
            messagebox.showerror("Inspection failed", str(error))

    def _set_result(self, status):
        self.result_text.set(status)
        colors = {"OK": "#15803d", "NG": "#b91c1c", "WAITING": "#64748b"}
        self.result_label.configure(bg=colors.get(status, "#64748b"))

    def _show_image(self, key, frame):
        label = getattr(self, key + "_label")
        if frame is None:
            label.configure(image="", text="No image")
            self._photos.pop(key, None)
            return
        height, width = frame.shape[:2]
        scale = min(
            self.PREVIEW_SIZE[0] / width,
            self.PREVIEW_SIZE[1] / height,
        )
        size = (max(1, int(width * scale)), max(1, int(height * scale)))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb).resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=image)
        self._photos[key] = photo
        label.configure(image=photo, text="")

    def _refresh_live_view(self):
        if self.camera is not None:
            frame = self.camera.get_frame()
            if frame is not None:
                self._show_image("live", frame)
            elif self.camera.get_error():
                self.status_text.set(self.camera.get_error())
        self.root.after(30, self._refresh_live_view)

    def _close(self):
        if self.camera is not None:
            self.camera.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
