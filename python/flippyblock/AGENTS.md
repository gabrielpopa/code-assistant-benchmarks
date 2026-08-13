## Large file handling

Do not use the write/edit tool to create or replace large files.

For files over ~500 lines:
- Prefer generating the file with a script, heredoc chunks, or smaller append operations.
- For modifications, make small localized edits instead of rewriting the whole file.
- Verify the result with:
  - `wc -l <file>`
  - language formatter/linter
  - relevant tests

use ask_user_question if you're unclear about something
