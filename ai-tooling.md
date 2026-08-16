# AI Tooling Disclosure

AI assistance was used to accelerate repository design, code generation, test design, synthetic policy drafting, documentation and defect analysis. The principal tool was OpenAI ChatGPT operating with GitHub repository access. The work was directed, tested and reviewed by the student, who remains responsible for correctness, security, academic integrity and the final presentation.

## Tools and uses

AI assistance was used for:

- translating the project brief into an implementation and compliance plan;
- proposing the explicit single-agent architecture;
- creating synthetic HR policies and records;
- implementing FastAPI, RAG, MCP client/server and evaluation code;
- adding tests and CI/CD;
- analysing failed deployment and workflow tests;
- drafting documentation and the demonstration script;
- reviewing the final repository against the assignment requirements;
- diagnosing and correcting the initial deterministic-only LLM and embedding gaps;
- integrating an OpenAI-compatible LLM refinement path and learned semantic embeddings through OpenRouter.

## What worked well

- Rapidly converting the written requirements into a traceable repository structure.
- Generating a coherent synthetic policy corpus and mock datasets without introducing real employee information.
- Producing repeatable unit, MCP protocol, deep-health and deployed-service smoke tests.
- Identifying defects from screenshots and workflow logs, including irrelevant citations and an incomplete prompt-injection pattern.
- Creating documentation, architecture explanations and a timed demo sequence that match the implemented workflows.
- Using automated regression tests before merging changes into `main`.
- Verifying the deployed LLM and semantic embedding paths from GitHub-hosted runners rather than relying only on configuration settings.

## What did not work well

- An early attempt packaged the application as Base64 archive fragments. The archive was corrupt and several bootstrap Actions failed. That approach was abandoned and replaced with normal, human-readable source files.
- A previous AI-generated status report overstated repository completion before the expanded source tree had been verified.
- A GitHub permission response of `read` was incorrectly treated as proof that `quantic-grader` had been explicitly added. For a public repository, that response does not prove collaborator invitation or acceptance. The repository settings now show the explicit invitation separately.
- The first prompt-injection rule did not match the phrase “ignore all previous instructions”; manual testing exposed the defect and regression tests were added.
- Initial citation filtering returned unrelated policy families for some queries; workflow-specific filters and tests corrected it.
- The first deployed architecture used deterministic answer synthesis and hashing TF-IDF vectors. That met many functional requirements but left a strict assignment-alignment risk because the brief asks for an LLM-based system and an embedding model. The deployment was subsequently upgraded and independently verified with a configured OpenAI-compatible LLM and learned semantic embeddings through OpenRouter.

## Final verified production state

The deployed version `2.1.0` uses:

- `openai/gpt-oss-20b:free` for constrained, evidence-grounded answer refinement;
- `nvidia/nemotron-3-embed-1b:free` for learned semantic policy embeddings;
- OpenRouter through environment-variable configuration;
- deterministic orchestration for tool selection, policy filtering, safety controls and confirmation gates;
- a local deterministic hashing embedding fallback for CI or provider outages.

The public deployment verification records successful provider calls and preserves provider/model information in non-secret health and operational-trace metadata. The model does not choose tools, approve actions or bypass policy controls.

## Human verification and accountability

Human verification included deploying the application to Render and manually testing the remote-work, benefits, prompt-injection and PTO confirmation workflows. Generated content was kept fictional and no real employee data or company secrets were introduced.

The 25-item evaluation uses deterministic rule-based proxy metrics for regression testing; it is not represented as an independent expert or LLM-judge assessment. The student remains responsible for the final repository, presentation, collaborator invitation, submission links and accurate description of limitations.
