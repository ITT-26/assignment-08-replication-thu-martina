# Documentation

[add references to .md files that talk about paper selection, implementation discussion, demo video link]

---
# Replication: CamIO
## CamIO Creator
### Run
Install the required packages:

```bash
pip install -r creator_requirements.txt
```

Start the Creator with the default template:

```bash
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

### Export

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

### On-screen instruction

#### Workflow

1. Launch the Creator from the terminal and optionally specify a template image. The selected template will be displayed.
2. Draw a hotspot by clicking around the object to create a polygon.
3. Press **Enter** to finish the polygon.
4. Enter a hotspot name in the dialog (or cancel to discard it).
5. Select the hotspot from the list on the left to edit its properties:
   - Name
   - Description
   - Audio (browse for an existing file or record directly)
6. Press **Save changes** to export the project.

#### Interface

- **Left panel**
  - Displays all created hotspots.
  - Select a hotspot to edit it.
  - Delete removes the selected hotspot.

- **Center**
  - Shows the selected template image.
  - Click to place polygon vertices around the desired object.
  - Use the mouse wheel to zoom in or out for more precise drawing.
  - Press **Enter** to finish the polygon.
  - Press **Esc** to cancel the current polygon.

- **Right panel**
  - Edit the hotspot's name and description.
  - Browse for an existing audio file or record a new one.
  - Save changes exports the project.

---
## CamIO Explorer
[complete]

---
# Disclaimer - AI Usage
[complete]