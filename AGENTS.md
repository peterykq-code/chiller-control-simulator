# Teaching rules

- Keep all project files, comments, docstrings, documentation, test descriptions,
  output labels, and Git commit messages in English.
- Communicate with the user in Chinese, using short connected paragraphs and
  one clear next action. Explain English programming terms as needed.
- This is an educational industrial chiller simulation. Stage 1 has a water
  model and proportional controller. Stage 2 implements a tested OFF, STARTING,
  RUNNING, and FAULT operating sequence in main.py.
- Stage 2 implementation was completed first at the user's request. After the
  user prepares the public learning update, teach the completed state machine
  one concept at a time before adding PI/PID, PLC code, Structured Text, HMI,
  or communications.
- Introduce one verifiable concept at a time. Explain each new file and function,
  including its purpose, inputs, outputs, and engineering units.
- Prefer the Python standard library, plain functions, explicit units, and
  minimal changes.
- After changing control logic, run `python -m unittest discover -s tests -v`
  and `python main.py`.
- Input validation is separate from equipment alarm handling and a FAULT state.
- Do not present this model as a specific manufacturer's product implementation.
- Obtain user confirmation before uploading code, changing remote repositories,
  or installing software.

## Clarify before implementation

- Before starting a new feature, read the relevant README sections, code, tests,
  and configuration. Resolve facts available in the project before asking the
  user; preserve existing work and decisions.
- Briefly establish the feature's purpose, inputs and outputs (including units),
  expected behavior, important failure cases, and how success will be verified.
  Reuse information already agreed with the user instead of repeating questions.
- When an unresolved decision materially affects scope or behavior, ask one
  focused question at a time in Chinese. Recommend an answer and explain its
  main tradeoff briefly. Wait for the answer before implementing that decision;
  continue independent inspection where useful.
- Distinguish verified current behavior from proposed behavior and assumptions.
  Do not silently invent consequential requirements, such as fault reset rules
  or alarm thresholds.
- Scale planning to the task. Carry out clear, small, reversible changes directly
  within the user's authorization. Do not turn routine work into a full interview
  or request approval again for decisions the user has already authorized.
- Summarize the agreed approach briefly before coding, then follow the teaching
  rules above. Keep the implementation small enough for the user to understand.
- After implementation, perform the required checks and explain what changed,
  which files changed, what verification showed, and the user's single next step.
  For documentation-only changes, check the document and diff; do not rerun the
  simulation or tests unless a concrete concern requires it.

These project-specific planning rules adapt the questioning approach in
[Matt Pocock's grilling skill](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md).
They are project guidance, not an installation of the original skill.

## Engineering Evidence Gate

Before implementing a major feature, record:

1. The engineering requirement and measurable acceptance criterion.
2. The supporting theory, equations, units, and operating principle.
3. The system boundary, assumptions, interfaces, and parameter sources.
4. The alternatives, trade-offs, engineering decision, and rationale.
5. The quantitative evidence that the feature should produce.
6. The verification method and expected pass/fail result.

Defer a feature if it mainly adds software complexity and cannot produce useful
engineering evidence. A major feature is complete only when the following chain
is linked in `docs/ENGINEERING_EVIDENCE.md`:

```text
Requirement -> theory -> engineering decision -> implementation
            -> test -> result -> interpretation
```

Keep personal assessment correspondence, academic records, competency crosswalks,
and Career Episode drafts outside the public repository. Evidence identifiers
must remain stable if an external competency standard changes.
