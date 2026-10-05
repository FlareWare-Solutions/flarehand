# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | Yes |
| Older | No |

## Report a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: open the repository's **Security** tab and select
**Report a vulnerability**. This creates a private advisory that only the maintainers can see.

Include what you found, the steps to reproduce it, and the version or commit. Name the tool you
ran flarehand in, such as Claude Code, Codex, Cursor, Gemini CLI or Copilot.

We aim to acknowledge a report within 3 working days, and to agree a fix and a disclosure date with
you within 30 days. We credit reporters in the advisory unless you ask us not to.

## What counts

- A hook or script that runs code, reads files or sends data beyond what
  [privacy and data](docs/privacy-and-data.md) describes.
- Anything that writes to the knowledge base without the person's yes.
- A way for a crafted source, playbook or `.flarehand/` folder to run commands or leak data.
- The redaction scan missing a credential format it claims to catch.

flarehand sends no telemetry. Your agent sends your conversation to its own model provider, which
is outside this project's control.
