# FlippyBlock hard evaluator

This directory evaluates output produced from
`python/flippyblock/instructions_hard.md`. Keep it outside the model's mounted task
directory.

After the model creates `python/flippyblock/main.py`, install pygame in the
operator environment and run from the repository root:

```bash
python3 evaluators/python/flippyblock_hard/run_tests.py python/flippyblock
```

The runner prints a passed/total automated score and individual failures. It checks
source structure and specification markers, rejects forbidden dependencies and
files, and launches the game for 1.5 seconds using SDL's headless video driver to
detect startup crashes.

Then complete [MANUAL_REVIEW.md](MANUAL_REVIEW.md). Visual quality, accurate
hitboxes, input feel, pause behavior, and deterministic sequences require human
observation and should not be inferred from source-text checks alone.

Report both scores, for example:

```text
Automated: 40/40
Manual: 12/12
```
