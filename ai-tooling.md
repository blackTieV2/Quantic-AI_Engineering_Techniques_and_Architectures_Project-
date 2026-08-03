# AI Tooling Disclosure

AI assistance was used to accelerate repository design, code generation, test design, synthetic policy drafting, documentation and defect analysis. The principal tool was OpenAI ChatGPT operating with GitHub repository access. The work was directed and reviewed by the student, who remains responsible for correctness, security, academic integrity and the final presentation.

## Tools and uses

AI assistance was used for:

- translating the project brief into an implementation and compliance plan;
- proposing the explicit single-agent architecture;
- creating synthetic HR policies and records;
- implementing FastAPI, RAG, MCP client/server and evaluation code;
- adding tests and CI/CD;
- analysing failed deployment and workflow tests;
- drafting documentation and the demonstration script;
- reviewing the final repository against the assignment requirements.

## What worked well

- Rapidly converting the written requirements into a traceable repository structure.
- Generating a coherent synthetic policy corpus and mock datasets without introducing real employee information.
- Producing repeatable unit, MCP protocol, deep-health and deployed-service smoke tests.
- Identifying defects from screenshots and workflow logs, including irrelevant citations and an incomplete prompt-injection pattern.
- Creating documentation, architecture explanations and a timed demo sequence that match the implemented workflows.

## What did not work well

- An early attempt packaged the application as Base64 archive fragments. The archive was corrupt and several bootstrap Actions failed. That approach was abandoned and replaced with normal, human-readable source files.
- A previous AI-generated status report overstated repository completion before the expanded source tree had been verified.
- A GitHub permission response of `read` was incorrectly treated as proof that `quantic-grader` had been explicitly added. For a public repository, that response does not prove collaborator invitation or acceptance.
- The first prompt-injection rule did not match the phrase “ignore all previous instructions”; manual testing exposed the defect and regression tests were added.
- Initial citation filtering returned unrelated policy families for some queries; workflow-specific filters and tests corrected it.
- The current deployed release uses deterministic synthesis unless an external OpenAI-compatible provider is configured. This is a remaining alignment issue because the brief asks for a working LLM-based system.
- The current hashing TF-IDF representation is lightweight and reproducible, but it may be judged less favorably than a learned local or hosted embedding model.

## Human verification and accountability

Human verification included deploying the application to Render and manually testing the remote-work, benefits, prompt-injection and PTO confirmation workflows. Generated content was kept fictional and no real employee data or company secrets were introduced.

The deterministic evaluation is reproducible but uses rule-based proxy metrics; it is not represented as an independent expert or LLM-judge assessment. The student remains responsible for reviewing the final repository, configuring any required model provider, confirming grader access, recording the presentation and accurately describing limitations during the demo.