# Clarification policy

- Never guess at requirements. If more than one reasonable interpretation
  of my request exists, use AskUserQuestion before writing any code.
- Ask before: choosing a library or framework not already in the project,
  creating new files or directories, changing the public API of a function,
  deleting or renaming anything, modifying config/CI/build files.
- If a file, path, env var, or command I mention doesn't exist, stop and ask.
  Do not create a plausible substitute.
- If a test fails for a reason I didn't describe, report it and ask before
  "fixing" surrounding code.
- When a task has >1 viable approach with different tradeoffs, present the
  options and wait for my choice. Don't pick one and proceed.
- State assumptions explicitly at the top of your answer when you do have to
  make one. Mark them as ASSUMPTION: so I can catch them.
