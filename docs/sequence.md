# Sequence - hyred

```mermaid
sequenceDiagram
    Recruiter->>App: Screen Candidate
    App->>Ontology: Check Ethical Lattice
    Ontology-->>App: Clearance
    App->>Matcher: Calculate Pastyche Fit
    Matcher-->>Recruiter: Matching Score
```
