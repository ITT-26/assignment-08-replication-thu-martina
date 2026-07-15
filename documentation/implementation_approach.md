# Implementation Approach

Our goal was not to reproduce the complete CamIO-Web system, but to implement its main interaction technique: creating interactive hotspot regions on an image and later exploring a printed version through camera-based pointing gestures.

To make the implementation manageable within the assignment period, we divided the project into two independent applications: **Creator** (Thu) and **Explorer** (Martina).

## Creator

The Creator application is responsible for preparing interactive templates.

Users first select a template image. If it is the first time the image is used, they are asked to provide a project name; otherwise, the project information is loaded automatically from a previous session. Hotspots are created by clicking around an object to define a polygonal region; pressing [ENTER] finishes the polygon and prompts the user for a hotspot name, while [ESC] or [BACKSPACE] can be used to cancel the current drawing or undo the last point. Once created, a hotspot's shape can still be adjusted by dragging its individual vertices directly on the canvas, and existing hotspots can be selected either from the sidebar list or by clicking on their polygon in the canvas. The canvas also supports zooming and panning, to make it easier to place vertices precisely on more detailed templates.

Each hotspot is automatically assigned a default color to visually distinguish it from the others, though this color can be manually changed from the property panel if desired. Additional properties - a description, an audio label, and the hotspot's name - can also be edited there: audio can either be recorded directly through the built-in microphone input or imported from an existing file. Hotspots can also be deleted, which removes both the region and its associated audio file, if any.

The application stores all hotspot information in a `project.camio.json` file. Each hotspot contains:
- name
- description
- polygon coordinates
- unique color
- audio file path

When exporting a project, the Creator automatically generates:
- the original template image
- a printable template with ArUco markers (both png and pdf formats)
- a color map image
- the project JSON
- recorded audio files

The color map encodes every hotspot using a unique solid color. Instead of performing expensive point-in-polygon calculations during runtime, the Explorer only needs to read the color of the corresponding pixel to identify the selected hotspot.

### Tools and Libraries

- PySide6 (Qt) — GUI framework used for the main window, canvas, and property panel.
- Pillow (PIL) — image loading and processing for the template, printable template, and color map.
- OpenCV (`cv2.aruco`) — used only to generate the ArUco markers embedded in the printable template.
- img2pdf — converts the printable PNG template into a PDF with a fixed DPI layout, to guarantee physical A4 dimensions when printed.
- sounddevice / soundfile — audio recording (via microphone) and file I/O for hotspot audio labels.
- NumPy — array handling for recorded audio data.

## Explorer

The Explorer application allows users to interact with the printed template. After selecting a template and a camera, the application continuously performs the following steps:

1. Board detection: detect the four ArUco markers in the camera frame and compute their centroid positions, sorted geometrically (top-left, top-right, bottom-left, bottom-right) based on their position in the frame rather than their marker ID.
2. Perspective transformation: use the four marker positions to compute a perspective transformation matrix mapping the camera view to the template's coordinate space, matching the layout produced by the Creator's export (same margins and marker placement).
3. Warping: apply the transformation to the camera frame to obtain a top-down, undistorted view of the template ("warped frame"), matching the dimensions of the exported color map.
4. Hand detection: detect the user's hand using MediaPipe and estimate whether the fingers form a pointing gesture (index extended, other fingers flexed).
5. Coordinate mapping: transform the pointing position from camera coordinates into template coordinates, using the same perspective transformation computed in step 2.
6. Hotspot lookup: read the pixel color at the mapped position from the exported color map and match it to the corresponding hotspot.
7. Feedback: play the hotspot's associated audio and highlight the region on the warped view.

Steps 1–3 (board detection and transformation) run on every frame.

### Tools and Libraries

- pyglet — window creation and rendering of the camera feed / warped template.
- OpenCV (`cv2`, `cv2.aruco`) — ArUco marker detection, perspective transformation, and frame warping.
- MediaPipe (Tasks API) — hand landmark detection, used for pointing gesture recognition.
- Pillow (PIL) — used internally to convert OpenCV frames into a format pyglet can display.
- sounddevice / soundfile — playback of hotspot audio labels.
- NumPy — coordinate and array operations throughout the pipeline.

## Integration

The two applications communicate only through the exported project files.
The Creator produces all files required by the Explorer, including the JSON metadata, printable template, color map, and audio files. Because of this file-based workflow, both applications can be developed independently while remaining fully compatible after integration.
This modular design also made debugging easier, since the Creator could be tested separately from the Explorer before performing end-to-end testing.

## Differences from the Original System

While our prototype follows the core interaction proposed in the paper, several implementation decisions differ from the original system.

The original system relies on template matching to locate the TG within the camera feed: the digital template image is compared against regions of the incoming camera frame to find the best match, without requiring any physical markers on the printed material. Because this operation is computationally expensive, it is not run on every frame in the original system, but at a fixed interval. Instead of using this method for template localization, we use four ArUco markers together with a perspective transformation, which provide a simpler solution that could be implemented within the assignment period.

Furthermore, our Creator is implemented as a desktop application using Python and PySide6 rather than as a browser application.

We also extended the export functionality by generating a printable A4 template with ArUco markers and a PDF version to simplify printing.

Finally, our implementation focuses on reproducing the essential interaction workflow instead of all features of the original CamIO-Web system. This is consistent with the assignment requirement to replicate the interaction technique rather than develop a feature-complete copy.

## Limitations

- Preparing a template requires a sighted user to define hotspots with the Creator application and print the resulting template; the system does not support any form of independent template preparation by BVI users (this is also a limitation in the original project).
- Our prototype demonstrates the interaction technique using flat printed images rather than genuine tactile graphics. Testing with true tactile materials remains future work.
- Board registration currently relies entirely on the four ArUco markers being printed on the template. If the user's hand or finger occludes one of the markers while pointing, the perspective transformation cannot be computed and the pointing position is lost until the marker is visible again. A more robust approach, other than the one used in the original system, could use general-purpose computer vision techniques (e.g. contour or template matching, discussed during the course) to detect the printed sheet independently of dedicated markers.
- The current Explorer only plays the hotspot's associated audio label; the optional textual description stored in each hotspot is exported to the project JSON but never used at runtime (no on-screen text, no text-to-speech). The original system supports reading the full textual description aloud via the built-in speech synthesizer.
- The Creator does not currently allow assigning the same color to multiple polygons that represent the same conceptual region, nor does it validate that colors in the color map are unique across hotspots, which could lead to lookup collisions in the Explorer (users can manually make sure that the colors are not repeated).

## Difficulties

- Coordinate mapping between Creator and Explorer: hotspot polygons are defined by the Creator in the original template's coordinate space, but the color map and printable template are generated in a different, scaled and offset coordinate space (to fit the fixed A4 canvas with margins for the ArUco markers). Initially, this mismatch caused hotspot polygons to be misaligned with their intended position in the color map. We resolved this by extracting the scale/offset calculation into a shared helper function, used consistently whenever a coordinate needs to move between the original template space and the printable/color map space, both in the Creator's export step and in the Explorer's hotspot loading step.
- Template printing: printing the exported PNG template directly did not reliably preserve the physical A4 dimensions, since it depended on printer defaults and scaling settings, which broke the correspondence between the physical marker size/position and the one assumed by the Explorer. We resolved this by generating a PDF version of the printable template with a fixed DPI layout, guaranteeing the physical page size at print time regardless of printer settings.

## Demo Preparation

Ahead of the presentation, we ran a full end-to-end test of the system: creating a project from scratch in the Creator (defining hotspots, naming them, and recording audio), exporting and printing the resulting template, and then using the Explorer to point at the printed template and confirm that the correct audio label played for each region.

Audio recording directly through the Creator's built-in microphone input works correctly. However, for the demo itself we chose to instead generate the hotspot audio labels using the Google Text-to-Speech library, to ensure clearer and more consistent audio quality during the presentation.