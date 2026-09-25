# Local Qwen lane

Proposals only. This client calls an OpenAI-compatible chat endpoint and
prints the reply. It does not commit, merge, or write a ROM or extracted
assets. Jeff merges. Nothing from this lane is an in-game result.

The host and the model are environment variables. They are not stored in
the script.

```sh
export QWEN_BASE_URL=http://homelab70:11434/v1   # example only; Ollama
export QWEN_MODEL=qwen3.8:27b                     # example only
# export QWEN_API_KEY=...                         # optional; Ollama usually needs none
```

`QWEN_BASE_URL` is the API root, including `/v1`. The client posts to
`${QWEN_BASE_URL}/chat/completions`.

```sh
python3 tools/qwen/qwen_client.py function-naming --input symbols.txt
python3 tools/qwen/qwen_client.py crash-triage --input crash.log
python3 tools/qwen/qwen_client.py doc-draft --input notes.md
python3 tools/qwen/qwen_client.py test-review --input test_out.txt
```

`--dry-run` prints the request JSON and does not open a connection. Use it
to confirm the URL and model are the ones you exported.

| Task | Prompt | Use |
| --- | --- | --- |
| `function-naming` | `prompts/function_naming.md` | Bulk rename proposals. Keep `func_*` when the evidence is thin. |
| `crash-triage` | `prompts/crash_triage.md` | Log and crash excerpts. |
| `doc-draft` | `prompts/doc_draft.md` | Doc drafts from notes you already have. |
| `test-review` | `prompts/test_output_review.md` | Test or build logs. A green compile is not a playtest. |

The tracking issue for a naming pass is
https://github.com/Jhalvordson/RogueSquadron64Recomp/issues/10.
This scaffold does not perform that pass.
