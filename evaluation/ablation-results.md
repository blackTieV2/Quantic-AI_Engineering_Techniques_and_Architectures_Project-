# Retrieval Ablation

The comparison changes chunk size and overlap while keeping the deterministic embedding model and query set fixed.

| Configuration | Chunk words | Overlap | Hit@3 | Hit@5 | MRR | Chunks |
|---|---:|---:|---:|---:|---:|---:|
| compact | 60 | 10 | 1.0 | 1.0 | 0.9 | 212 |
| balanced | 120 | 20 | 1.0 | 1.0 | 0.95 | 126 |
| broad | 220 | 30 | 1.0 | 1.0 | 0.95 | 126 |

Selected configuration: **balanced** because it produced the strongest Hit@3/MRR trade-off in this deterministic test.
