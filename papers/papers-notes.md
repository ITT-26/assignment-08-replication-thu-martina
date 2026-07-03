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





---

### [Textoshop: Interactions Inspired by Drawing Software to Facilitate Text Editing](Textoshop.pdf)

Damien Masson, Young-Ho Kim, and Fanny Chevalier. 2025. Textoshop: Interactions Inspired by Drawing Software to Facilitate Text Editing. Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems (CHI '25). https://doi.org/10.1145/3706598.3713862

#### What is the paper about?

Textoshop explores a new way of editing text by borrowing interaction techniques from drawing and image editing software such as Adobe Photoshop. Instead of relying on traditional text-editing operations (select, cut, copy, paste), text fragments become directly manipulable objects that can be dragged, resized, rotated, combined, or edited using tools such as brushes and layers. Large Language Models (LLMs) act as the backend that interprets these interactions and rewrites the selected text while preserving the user's intent.

#### Notes on 2-week implementation for ITT

##### Possible interactions to replicate

**Direct Manipulation**

- Drag & Drop text fragments
> Instead of cut + paste, users can directly drag selected text fragments to a new position.

- Resize
> Dragging the resize handle expands or shortens the selected text. We could map the resize amount to prompts such as "expand" or "summarize" using an LLM.

- Rotate
> Rotating a text fragment changes its sentence structure while preserving the meaning. We could use an LLM to rewrite the sentence with a different clause order or voice.

---

**Text Editing Tools**

- Tone Picker + Tone Brush
> Users choose a writing style (e.g., formal/informal, positive/negative, simple/complex) and paint over text to apply it. We could implement this with a few sliders and generate a prompt based on their values.

- Tone Eyedropper (optional)
> Similar to Photoshop's eyedropper: sample the writing style from one paragraph and apply it to another.

- Repair Tool (optional)
> Brush over text to fix grammar and spelling.

---

##### Possible implementation

Frontend

- Simple text editor (HTML + JavaScript or PyQt)
- Text fragments represented as draggable objects
- Resize and rotation handles
- Tone picker with sliders

Backend

- LLM API (OpenAI or Gemini)
- Prompt templates for:
  - expand
  - summarize
  - reorder sentence
  - change writing style

Example mapping

- Drag → Move text (no AI required)
- Resize larger → Expand text
- Resize smaller → Summarize text
- Rotate → Reorder sentence while preserving meaning
- Tone Brush → Rewrite text according to selected writing style

##### Some thoughts

- The contribution of the paper is the interaction technique rather than the LLM itself.
- We do not need to replicate the complete editor. Implementing two or three core interactions should already demonstrate the main idea.
- The most interesting interactions seem to be Resize, Rotate, and Tone Picker, since they connect geometric manipulations with semantic text editing.
- The biggest challenge is likely prompt engineering rather than programming. We need prompts that produce consistent results for different interaction strengths.
- Using an existing LLM API (e.g., OpenAI or Gemini) should be sufficient since the paper itself also relies on an existing LLM backend.





----
### Paper
#### What is the paper about?
#### Notes on 2-week implementation fot ITT

