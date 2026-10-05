# setup-workstation - building a developer machine

**Scope.** The common pieces of a developer machine: a package manager, git, Python, Node, an editor
and SSH keys, on Windows, macOS and Linux. For Python in detail, read `setup-python.md`. For flarehand
in an AI tool, read `setup-ai-tools.md`.

## Contents

- Check the machine first
- Route, do not rewrite
- What you can and cannot do for them
- A package manager
- Git
- Python
- Node
- An editor
- SSH keys
- Windows and WSL
- Access, which is often the real blocker
- New to the team

## Check the machine first

```bash
python3 scripts/doctor.py --capabilities
```

It reports the operating system and what is already installed. Windows, macOS and Linux differ in
software, paths and order. Giving someone the wrong platform's steps wastes an afternoon.

## Route, do not rewrite

If their team has its own setup guide, in a playbook, a repository README or a wiki they can reach,
that guide wins. Read it, confirm it matches the machine, and walk them through it. Give them the link
too, so they can follow along.

The steps below are general practice. Use them when no team guide exists, and say so once.

**Never state a version number from memory.** Have the package manager list what is available, then
pick from the list.

## What you can and cannot do for them

**You can** run checks, read the current procedure, tell them exactly what to click, confirm each step
worked, and work out which step failed.

**You cannot** click through a graphical installer, type an administrator password, or approve a
security prompt. Say so plainly when you reach one, give the exact steps, and wait for them to confirm
before carrying on.

Working through it one step at a time, confirming each one, is much faster than handing over a wall
of instructions. Most failures are one missed checkbox, and catching it at once saves the hour spent
finding it later.

## A package manager

Install everything else through one of these, so updates and removals stay simple.

| System | Package manager | Where to read about it |
|---|---|---|
| macOS | Homebrew | `https://brew.sh` |
| Windows | winget, built in on current Windows. Scoop is a per-user alternative. | `https://learn.microsoft.com/windows/package-manager/` |
| Debian, Ubuntu | apt | Built in |
| Fedora, RHEL | dnf | Built in |

Check first with `brew --version`, `winget --version`, `apt --version` or `dnf --version`.

## Git

```bash
git --version
```

If it is missing, install it with the package manager, or from `https://git-scm.com`. On macOS,
`xcode-select --install` brings git with the Command Line Tools.

Then set who they are, once per machine. Use the name and email their team expects on commits:

```bash
git config --global user.name "<their name>"
git config --global user.email "<their work email>"
```

Ask for both. Never fill them in from a guess.

## Python

Read `setup-python.md`. It covers every operating system and what to do on a locked-down machine.

## Node

Install Node through a version manager, not a system package, so each project can use the version it
needs. Common choices are nvm on macOS and Linux, and nvm-windows or fnm on Windows. The Node site,
`https://nodejs.org`, lists the current long-term support release.

```bash
node --version
npm --version
```

If a project has a `.nvmrc` or an `engines` field in `package.json`, use the version it names.

## An editor

Ask which editor they use or their team uses. Do not pick one for them. If they have none, VS Code is
a common free choice, and Cursor and the JetBrains IDEs are others. Install it through the package
manager or the vendor's own site.

## SSH keys

Most code hosts take an SSH key for git over SSH. Check for one first:

```bash
ls ~/.ssh
```

A file named `id_ed25519.pub` means they already have one. Otherwise make one:

```bash
ssh-keygen -t ed25519 -C "<their work email>"
```

Accept the default path, and set a passphrase. Then add the public key, the `.pub` file, to their
account on GitHub, GitLab or whichever host their team uses, under the SSH keys settings. Never ask
them to paste the private key anywhere, including into this conversation.

Test it with the host's own check, such as `ssh -T git@github.com`.

**HTTPS is fine too.** On GitHub, `gh auth login` signs in through the browser and handles git
credentials. Use whichever their team uses.

## Windows and WSL

Many teams develop on Windows inside WSL, the Windows Subsystem for Linux. If their team does, install
it once with `wsl --install` from an administrator PowerShell, then follow the Linux steps inside it.
Microsoft documents it at `https://learn.microsoft.com/windows/wsl/`.

Keep each tool on one side. Git, Node and Python installed in Windows are separate from the ones in
WSL, and mixing them is a common source of confusing errors.

## Access, which is often the real blocker

Several pieces need access granted rather than software installed: membership of the team's code
organisation, single sign-on, a database or environment, a shared drive. That is a request to their
team lead or IT team, not something to work around. Raise it early, because it takes time. Say which
specific access is needed and why, rather than describing the symptom.

## New to the team

If someone is new, ask whether their team has an onboarding guide. Point them at the whole guide,
not only the answer to the one question they asked. They usually do not know what to ask yet, and
a guide has its order for a reason. If there is none, offer to turn what they learn into one with the
`onboarding-plan` or `docs-page` template.
