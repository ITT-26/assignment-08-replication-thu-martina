# Replication: CamIO

## Documentation

See [paper_selection_process.md](documentation/paper_selection_process.md) for our paper selection process, and [implementation_approach.md](documentation/implementation_approach.md) for a detailed explanation of the implementation. 

A short demo video is available at [add link]().

## Project Structure

```text
CamIO_replication/
├── creator/            # CamIO-Creator (PySide6 app)
│   ├── app/            # main application code
│   └── assets/         # default template images
├── explorer/           # CamIO-Explorer (pyglet app)
├── templates/          # exported projects (Creator output, read by Explorer)
├── documentation/      # paper selection, implementation approach
└── papers/             # assignment + reference papers
```
---

## Implementation

### CamIO Creator

#### Run

Install the required packages:

```bash
pip install -r creator_requirements.txt
```

Start the Creator with the default template:

```bash
cd CamIO_replication
python camio_creator_launcher.py
```

Or specify another template image/microphone:

```bash
python camio_creator_launcher.py [--template TEMPLATE] [--mic MIC]
```

Supported input formats:

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)

If an exported project already exists for the selected template, it will be loaded automatically so editing can continue from the previous session.

---

#### Export

Press **Save changes** to export the current project.

A folder named after the template is created (or updated) inside the `templates` directory:

```text
templates/
└── <template_name>/
    ├── project.camio.json
    ├── color_map.png
    ├── printable_template.png
    ├── template.png
    └── audio/
```

The exported project can be opened directly by the Explorer application.

---

#### On-screen instruction

##### Workflow

1. Launch the Creator from the terminal and optionally specify a template image. The selected template will be displayed.
2. Draw a hotspot by clicking around the object to create a polygon.
3. Press [ENTER] to finish the polygon.
4. Enter a hotspot name in the dialog (or cancel to discard it).
5. Select the hotspot from the list on the left to edit its properties:
   - Name
   - Description
   - Audio (browse for an existing file or record directly)
6. Press **Save changes** to export the project.

##### Interface

- **Left panel**
  - Displays all created hotspots.
  - Select a hotspot to edit it.
  - Delete removes the selected hotspot.

- **Center**
  - Shows the selected template image.
  - Click to place polygon vertices around the desired object.
  - Use the mouse wheel to zoom in or out for more precise drawing.
  - Press [ENTER] to finish the polygon.
  - Press [BACKSPACE] to undo the last placed point.
  - Press [ESC] to cancel the current polygon.

- **Right panel**
  - Edit the hotspot's name and description.
  - Browse for an existing audio file or record a new one.
  - Save changes exports the project.

### CamIO Explorer

#### Run

Install the required packages:

```bash
cd CamIO_replication
pip install -r explorer_requirements.txt
```

Start the Explorer with the default template:

```bash
python camio_explorer_launcher.py
```

Or specify another exported template folder / camera:

```bash
python camio_explorer_launcher.py [--template TEMPLATE] [--camera CAMERA]
```

> **Note:** a printed template (exported and printed via the Creator, see above) is required before running the Explorer. We recommend pointing at the template using a phone camera rather than a laptop webcam, since it allows for a more natural top-down angle; apps like [Iriun Webcam](https://iriun.com/) let you use your phone as a regular webcam input.

#### Workflow

1. Launch the Explorer from the terminal, optionally specifying a template folder and camera index.
2. Point the camera at the printed template so that all four ArUco markers are visible; once detected, the application shows a top-down view of the template.
3. Explore the template freely with an open hand — no feedback is triggered.
4. Point at a region with your index finger extended (other fingers closed) to trigger its audio label.
5. Press 'q' or [ESC] to quit.

---

# Disclaimer - AI Usage

AI assistance was used at several points throughout the implementation, always with our own guidance and review. Specifically:

- `dialogs.py`: layout of the hotspot naming dialog.
- `app.py`: layout of the sidebar/inspector panels and the application stylesheet (`_apply_style`).
- `exporter.py`: use of the `img2pdf` library to generate a printable PDF with fixed physical dimensions.
- `camio_explorer.py`: the `fit_and_blit` helper function, and the hotspot highlight overlay (`cv2.fillPoly` / `cv2.addWeighted` in `draw_hotspot`).
- `hand_landmark_drawer.py`: drawing of hand landmarks and connections (`draw_hand`).

AI was also used to help draft and refine the documentation and this README file based on our own notes.