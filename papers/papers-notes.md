# Assignment 08 - Replication

Group members: Thu, Martina

## Finding suitable research papers

### [CamIO in the Browser - A Cross-Platform Audio Label Tool for Tactile Graphics](CamIO.pdf)

Dragan Ahmetovic, James Coughlan, Giorgio Dal Santo, Khadija Ezrouri, Matteo Manzoni, and Sergio Mascetti. 2025. CamIO in the Browser: A Cross-Platform Audio Label Tool for Tactile Graphics. In Adjunct Proceedings of the 27th International Conference on Mobile Human-Computer Interaction (MobileHCI '25 Adjunct). Association for Computing Machinery, New York, NY, USA, Article 21, 1–3. https://doi.org/10.1145/3737821.3748528

#### What is the paper about?

CamIO-Web is an open-source, browser-based audio labeling system for tactile graphics (TGs), designed to help blind and low-vision users explore physical drawings and diagrams. It consists of two components: CamIO-Creator, which lets a sighted user define labeled "hotspot" regions on a template image, and CamIO-Explorer, which runs in real time using template matching to locate the TG in the camera feed and the MediaPipe hand landmarker to detect a pointing gesture, mapping the touched location back to the template to play the corresponding audio label.

#### Notes on 2-week implementation for ITT

##### Parts of the system (CamIO-Web)
**CamIO-Explorer**

- Detection of the template area in the captured camera frame
> We can use the ArUco cardboard as our template area + perspective transformation, etc. (Assignment 4) if needed
- Hand detection + gesture detection (*pointing* in this case)
> We can use MediaPipe (Assignment 7)
- Getting coordinates where the user pointes
- Mapping coordinates to template
- Highlighting selected area + audio feedback

**CamIO-Creator**

Their software also has a feature that allows users to label their own TGs. The exported data includes:
- the template (an image of the TG)
- a list of hotspot areas, each repreesenting a specific region of the TG and associated with a title, a color, a textual description and an audio file (optional)
- a color map: an image file used to encode the position of the hotspot areas (used to represent the position of each hotspot area through its associated color)

> I think we should be able to replicate this in a similar way using pyglet and what we have learned. We could try to open a template with a drawing of our choosing, let the users select n points to create an area, and when a key like [ENTER] is pressed, they could add a label, specify a color and the mic could open to record the audio. After all areas have been selected, we could save everything using a key like 's'. Add other controls such as discarding changes.
> 
> Maybe we can include the PDF to print in the exports, and add the ArUco markers for easier mapping later.

##### Some thoughts
- Is it an interaction technique itself? No. But the tool uses camera-based pointing interaction.
- Using our laptops' webcams might be difficult if we want users to be able to point at the template while it is laying on top of a horizontal surface such as a table (and this is the way it would make sense to use the system I think, since it is intended for visually-impaired people). We could try to use our phones as input devices and a tripod, or somethig along these lines.
- Watch the resolution/scale consistency between digital template and the printed+photographed version for correct mapping.

### Paper
#### What is the paper about?
#### Notes on 2-week implementation fot ITT

