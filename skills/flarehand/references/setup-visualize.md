# setup-visualize - seeing your knowledge base as a graph

**Scope.** Opening the knowledge base in a tool that draws the connections. Entirely optional. For the
notes themselves, read `memory.md`.

## Do you need this

No. The knowledge base is plain markdown. Every command in `kb.py` works without any of this, and
`kb.py neighbors` already walks the links from the command line.

What a graph view adds is the accidental discovery. Seeing that three support cases all connect to one
configuration note is the kind of thing you notice by looking, not by searching.

Offer it. Do not push it.

## Obsidian

Free for work use. In February 2025 the commercial licence became optional, and the wording is that
anyone can use Obsidian for work, for free. There is no company size threshold. A paid licence exists
and is voluntary support, not a requirement.

**Setting it up takes one step.**

1. Install Obsidian from `https://obsidian.md`.
2. Open it and choose **Open folder as vault**.
3. Paste the path rather than browsing to it. The folder starts with a dot, so the file picker hides
   it by default.
   - macOS: press Command, Shift and G together, then paste `~/.flareware/flarehand`.
   - Windows: paste `%USERPROFILE%\.flareware\flarehand` into the address bar at the top of the dialog.
4. Open the graph view from the left sidebar.

A vault whose folder name starts with a dot opened correctly when this was tested. Obsidian's help
does not document it, and the Obsidian version used for the test was not recorded. Obsidian skips
dot-folders *inside* a vault, which is a different rule, and it is where the common belief that this
fails comes from.

If a release refuses the folder, make a plain-named link to it and open that as the vault instead.

- macOS: `ln -s ~/.flareware/flarehand ~/flarehand-kb`
- Windows, in PowerShell: `cmd /c mklink /J "$env:USERPROFILE\flarehand-kb" "$env:USERPROFILE\.flareware\flarehand"`

Both point at the same files, so `kb.py` keeps writing to `~/.flareware/flarehand` and nothing moves.

**What draws the lines.** Links in the body of a note, written as `[[permalink|Title]]`. That is the
format `kb.py` writes, so the graph works with no extra effort. Tags appear as nodes rather than
links, and that setting is off by default.

**What you will see.** Each note is a dot, and each wikilink is a line between two dots. A note with
many lines is usually a system or a project that a lot of work rests on. Notes in `chains/` and
`people/` show up as well. The tables at the root, such as `glossary.tsv`, `observations.tsv` and
`sources.tsv`, are not markdown, so Obsidian lists them as files and leaves them out of the graph.
Obsidian hides `.index/` and `.git/`, which is right: they are rebuilt or kept by `kb.py`.

**Edit freely, then let `kb.py` catch up.** A note you change in Obsidian is still yours. The next
`kb.py` command sees the change and rebuilds the index in one line. Keep the frontmatter header
intact, because every write refuses a note whose header is missing or never closes.

**A team playbook is not a vault to open here.** It lives in a repo and holds templates and rules, not
notes, so a graph of it shows little. Read it in the repo, the same as any other file.

## If Obsidian is not an option

The files are plain markdown with standard links. Several tools read the same folder.

| Tool | Notes |
|---|---|
| VS Code with the Foam extension | Free. Offer it if `doctor.py` shows VS Code is installed. |
| Logseq | Free and open source, a different way of working with notes |
| Any editor | No graph, but everything is readable. Nothing is locked in. |

## One thing worth saying out loud

Keeping the knowledge base out of `Documents` is deliberate. On Windows, OneDrive quietly redirects
Desktop, Documents and Pictures. A knowledge base that moves without warning is worse than one that
is slightly harder to find.

The trade is that nothing backs it up. Tell them that plainly and let them decide. Some people will
want a copy somewhere, and that is their call to make, not yours.

Do not set the hidden attribute on the folder on Windows. Obsidian ignores it, and it makes some
backup tools skip the folder entirely.
