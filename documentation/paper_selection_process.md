## Paper Selection Process

Before starting the implementation, we searched for recent HCI papers that proposed interesting interaction techniques while still being realistic to replicate within the two-week assignment period. Our main criterion was to choose a project whose core interaction could be implemented with the knowledge and tools we had learned during the course.
After reading several papers, we shortlisted two candidates: **CamIO in the Browser** and **Textoshop**.

### Textoshop

Textoshop proposes a novel text editing interface inspired by drawing software such as Adobe Photoshop. Instead of editing text through traditional operations like cut, copy, and paste, users directly manipulate text fragments using interactions such as dragging, resizing, rotating, or painting over the text. For example, resizing a text selection can expand or summarize its content, while painting with different colors can change its writing style, tone, or emotional expression. These interactions are interpreted by a Large Language Model, which rewrites the text according to the user's manipulation.
We found this interaction technique very interesting. However, replicating it would require implementing a custom text editing interface together with an LLM backend and carefully designing prompts to produce consistent results. Since much of the work would focus on prompt engineering rather than interaction implementation itself, we considered it relatively risky within the available time.

### CamIO in the Browser

CamIO is an audio labeling system for tactile graphics consisting of two applications: **Creator**, which allows a user to define interactive hotspot regions on an image, and **Explorer**, which detects a pointing gesture on a printed template and plays the corresponding audio label.
We considered this project much more suitable for the assignment because many of its core components could be implemented using techniques we had already learned during the course. In particular, the project combines ArUco marker detection and perspective transformation for template localization, MediaPipe for hand tracking and pointing gesture detection, OpenCV for coordinate mapping, and audio recording/playback using Python libraries. Rather than learning entirely new technologies, we could focus on integrating these components into a complete interactive system.
Another advantage was that the project could naturally be divided into two independent parts. One team member could work on the Creator application while the other developed the Explorer application, allowing both parts to be implemented in parallel and integrated afterwards.

### Final Decision

We ultimately selected **CamIO in the Browser** because it provided a good balance between novelty and feasibility. The project demonstrates an interesting camera-based interaction technique while remaining achievable within the assignment timeline. It also allowed us to build upon techniques from previous ITT assignments and combine them into a complete working prototype rather than implementing isolated individual components.