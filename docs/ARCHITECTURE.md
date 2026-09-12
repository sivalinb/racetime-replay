# Architecture

```mermaid
flowchart LR
    V[Exported runner video] --> CV[OpenCV frame and motion analysis]
    W[CSV GPX Health XML] --> P[Validated workout samples]
    CV --> A[Offset and nearest-sample alignment]
    P --> A
    A --> E[Candidate events and coverage]
    E --> UI[Synchronized replay and human review]
    E --> R[Event and knowledge retrieval]
    R --> G[Bounded LangGraph investigator]
    G --> S[Reference and policy validation]
    S --> UI
    G -. opt-in aggregate evidence .-> L[Cloud draft for review]
    E --> Q[Local evaluation and node traces]
```

The player and all numerical analysis run on the Python application's host. No raw media is sent by the optional synthesis path. Scene recognition and training optimization belong to the future roadmap, not this architecture's implemented measurement path.
