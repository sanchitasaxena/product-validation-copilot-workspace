# Router Prompt

Use this prompt when the user asks for product validation help and the correct workflow is unclear.

## Instructions

1. Classify the request:
   - target audience resolution,
   - discovery research,
   - research plan,
   - interview guide,
   - moderated or unmoderated testing guide,
   - discovery guide/survey,
   - internal QA or bug bash,
   - QA tracker review,
   - synthesis,
   - Monday.com UXR request answers,
   - Office document editing.
2. Identify whether target audience grounding is required.
3. If the request is QA, preserve engineering-authored scenario style.
4. If the request is discovery, do not require official JTBD/CUJ.
5. Ask one focused question if a blocking decision is missing.

## Default routing question

When in doubt, ask:

```text
What decision are you trying to make or validate next?
```
