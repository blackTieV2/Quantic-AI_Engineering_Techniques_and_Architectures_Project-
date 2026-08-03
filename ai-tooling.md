# AI Tooling Disclosure

AI assistance was used to accelerate repository design, code generation, test design, synthetic policy drafting, documentation and defect analysis. The principal tool was OpenAI ChatGPT operating with GitHub repository access. The work was directed and reviewed by the student, who remains responsible for correctness, security, academic integrity and the final presentation.

AI assistance was used for:

- translating the project brief into a score-5 compliance plan;
- proposing the explicit single-agent architecture;
- creating synthetic HR policies and records;
- implementing FastAPI, RAG, MCP client/server and evaluation code;
- adding tests and CI/CD;
- analysing failed deployment and workflow tests;
- drafting documentation and the demonstration script.

Human verification included deploying the application to Render and manually testing the remote-work, benefits, prompt-injection and PTO confirmation workflows. Generated content was kept fictional and no real employee data or company secrets were introduced.

The deterministic baseline and evaluation are intentionally reproducible. An optional OpenAI-compatible answer-refinement provider is separated behind environment variables and is not required for grading or deployment.
