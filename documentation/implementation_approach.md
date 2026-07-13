# Implementation Approach

Our goal was not to reproduce the complete CamIO-Web system, but to implement its main interaction technique: creating interactive hotspot regions on an image and later exploring a printed version through camera-based pointing gestures.
To make the implementation manageable within the assignment period, we divided the project into two independent applications: **Creator** and **Explorer**.

## Creator

The Creator application is responsible for preparing interactive templates.
Users first select a template image. Hotspots are then created by clicking around an object to define a polygonal region. After pressing **Enter**, the user assigns a name to the hotspot. Additional properties, including a description, a unique color, and an optional audio recording, can be edited in the property panel.
The application stores all hotspot information in a `project.camio.json` file. Each hotspot contains:
- name
- description
- polygon coordinates
- unique color
- audio file path

When exporting a project, the Creator automatically generates:
- the original template image
- a printable template with ArUco markers
- a color map image
- the project JSON
- recorded audio files

The color map encodes every hotspot using a unique solid color. Instead of performing expensive point-in-polygon calculations during runtime, the Explorer only needs to read the color of the corresponding pixel to identify the selected hotspot.

## Explorer

The Explorer application allows users to interact with the printed template.
After selecting a template and a camera, the application continuously performs the following steps:
1. Detect the four ArUco markers.
2. Compute a perspective transformation to recover the template coordinates.
3. Detect the user's hand using MediaPipe.
4. Estimate the pointing position from the detected hand landmarks.
5. Transform the pointing position into template coordinates.
6. Read the corresponding pixel from the exported color map.
7. Match the detected color to a hotspot and play its associated audio file.
Visual feedback is also displayed by highlighting the detected hotspot while the audio is being played.

## Integration

The two applications communicate only through the exported project files.
The Creator produces all files required by the Explorer, including the JSON metadata, printable template, color map, and audio files. Because of this file-based workflow, both applications can be developed independently while remaining fully compatible after integration.
This modular design also made debugging easier, since the Creator could be tested separately from the Explorer before performing end-to-end testing.

## Differences from the Original System

While our prototype follows the core interaction proposed in the paper, several implementation decisions differ from the original system.
Instead of using template matching for template localization, we use four ArUco markers together with a perspective transformation. This provides a simpler and more robust solution that could be implemented within the assignment period.
Furthermore, our Creator is implemented as a desktop application using Python and PyQt rather than as a browser application.
We also extended the export functionality by generating a printable A4 template with ArUco markers and a PDF version to simplify printing.
Finally, our implementation focuses on reproducing the essential interaction workflow instead of all features of the original CamIO-Web system. This is consistent with the assignment requirement to replicate the interaction technique rather than develop a feature-complete copy.