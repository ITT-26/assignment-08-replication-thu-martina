# Paper Selection Process

Before starting the implementation, we searched for recent HCI papers that proposed interesting interaction techniques while still being realistic to replicate within the two-week assignment period. Our main criterion was to choose a project whose core interaction could be implemented with the knowledge and tools we had learned during the course.

After reading several papers, we shortlisted two candidates: **[CamIO in the Browser - A Cross-Platform Audio Label Tool for Tactile Graphics](../papers/CamIO.pdf)** and **[Textoshop: Interactions Inspired by Drawing Software to Facilitate Text Editing](../papers/Textoshop.pdf)**.

## CamIO in the Browser

CamIO-Web is an open-source, browser-based audio labeling system for tactile graphics (TGs), designed for blind and low-vision users. It addresses a gap in existing camera-based audio-labeling systems, which tend to be closed, costly, or tied to specific hardware platforms. The system consists of two components: CamIO-Creator, which lets a sighted user define labeled "hotspot" regions on a template image, and CamIO-Explorer, which runs entirely in the browser and uses template matching to locate the TG within the camera feed together with the MediaPipe hand landmarker to detect a pointing gesture, playing back the corresponding audio label when the user touches a hotspot on the physical, printed version of the template.

We considered this project well suited for the assignment because several of its core building blocks overlapped with techniques already covered in the course - most notably hand tracking and gesture detection with MediaPipe, coordinate mapping - meaning we could focus on integrating these components into a complete interactive system rather than learning entirely new technology from scratch. 

Another advantage was that the project could naturally be divided into two independent parts. One team member could work on the Creator application while the other developed the Explorer application, allowing both parts to be implemented in parallel and integrated afterwards.

## Textoshop

Textoshop proposes a novel text editing interface inspired by drawing software such as Adobe Photoshop. Instead of editing text through traditional operations like cut, copy, and paste, users directly manipulate text fragments using interactions such as dragging, resizing, rotating, or painting over the text. For example, resizing a text selection can expand or summarize its content, while painting with different colors can change its writing style, tone, or emotional expression. These interactions are interpreted by a Large Language Model, which rewrites the text according to the user's manipulation.

We found this interaction technique very interesting. However, replicating it would require implementing a custom text editing interface together with an LLM backend and carefully designing prompts to produce consistent results. Since much of the work would focus on prompt engineering rather than interaction implementation itself, we considered it relatively risky within the available time.

## Final Decision

We ultimately selected **CamIO in the Browser** because it offered a good balance between novelty and feasibility. The project presented an interesting camera-based interaction technique while appearing achievable within the assignment timeline. We also expected to be able to build upon techniques from previous ITT assignments, combining them into a complete working prototype rather than implementing isolated individual components.

> Our notes and thought process while looking for papers and evaluating them can be found in the document [notes.md](../papers/notes.md).

## Note
It is relevant to point out that once we identified CamIO as a highly feasible option, we did not extensively continue searching for or comparing additional papers. This was a deliberate decision: given the two-week timeframe and the fact that this assignment overlapped with other end-of-semester coursework, we prioritized starting implementation early over broadening the search further.

