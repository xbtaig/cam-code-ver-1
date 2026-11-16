# Cam Code Ver 1 — Visual Parts Inspector

A Python desktop app for checking a wiring/connector assembly against a saved, known-good webcam image. It displays **OK** when no changes exceed the configured thresholds and **NG** when changed regions are found; changed regions are highlighted in red.

## Run in Visual Studio Code

1. Install Python 3.10 or later and the Python extension in VS Code.
2. Open this folder in VS Code, then open a terminal in the project folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies and launch the app:

   ```powershell
   python -m pip install -r requirements.txt
   python main.py
   ```

   You can also select **Visual Parts Inspector** in VS Code's Run and Debug panel.

## Basic use

1. Fix the webcam so the assembly stays in the same position, focus, and lighting.
2. Select a camera device index (usually `0`) and click **Connect / restart**. This is an OpenCV camera index, not a COM port; ordinary webcams do not use serial COM ports for video.
3. Place a known-good assembly in the view and click **Capture master**. The master is saved at `data/samples/master.jpg`. Alternatively, load an image to use as the master.
4. Click **Save live photo** to save the current camera frame in `data/captures/`.
5. Place the part to check in the same position and click **Inspect part**.
6. Adjust **Sensitivity** and **Min area** if small lighting or camera noise causes false NG results. Every inspection image and its CSV record are stored in `data/results/`.

## Project layout

```text
main.py                       Application entry point
scanner_app/
  core/camera.py              Webcam capture
  core/scanner.py             Image comparison and changed-area highlighting
  core/storage.py             Photo, master sample, and inspection file storage
  ui/app.py                   Tkinter user interface
ai_m61_32s_blink/
  ai_m61_32s_blink.ino        Existing Arduino LED blink sketch
data/
  samples/master.jpg          Saved good sample
  captures/                   Photos captured from the live camera
  results/                    Inspection images and inspection_log.csv
requirements.txt              Python dependencies
.vscode/launch.json           VS Code run configuration
tests/                        Image comparison and storage tests
```

This is a fixed-view image-difference inspector, not a trained object-recognition model. Camera movement, changed lighting, reflections, or part placement can affect the result. For reliable production checks, use stable lighting and a fixture that holds the camera and assembly consistently; tune the thresholds against known-good and known-bad parts.

Generated master samples, captured photos, and inspection results stay in the local `data/` folders and are excluded from the public repository.
