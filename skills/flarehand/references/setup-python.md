# setup-python - getting Python working, on any machine

**Scope.** Installing and checking Python 3, on Windows, macOS and Linux, for someone who has never
opened a terminal. For setting up flarehand in an AI tool, read `setup-ai-tools.md`. For the rest of a
developer machine, read `setup-workstation.md`.

## Contents

- Before you tell anyone to type anything
- Opening a terminal
- Windows
- macOS
- Linux
- Checking it worked
- When it is blocked
- Recording what you found

## Before you tell anyone to type anything

```bash
python3 scripts/doctor.py --check python --check os
```

It reports the operating system, the version, and every Python already on the machine. Read it first.
About half the time Python is already there and the whole install is unnecessary.

Two rules for this whole page.

**Never state a version number from memory.** Versions move. Have them list what is available, then
pick from the list. A hardcoded version fails in an odd way six months from now.

**Run what you can, hand over what you cannot.** You can run a check command. You cannot click through
an installer, and you cannot type an administrator password. Say clearly which parts are theirs.

## Opening a terminal

Not everyone has done this. It takes one sentence and saves ten minutes.

**Windows.** Press the Windows key, type `powershell`, and press Enter. A blue window opens.

**macOS.** Press Command and Space together, type `terminal`, and press Enter.

**Linux.** Ctrl, Alt and T together on most desktops.

## Windows

Work down this list. Stop at the first one that works.

**1. Check what is already there.**

```powershell
py -3 --version
python --version
```

Either printing the minimum `doctor.py` reports or higher means you are done. Skip to checking it
worked. `doctor.py` prints that minimum and is the only place the number lives.

If a Microsoft Store page opens instead, Windows is showing a placeholder rather than a real Python.
Carry on to the next step.

**2. The Python install manager from python.org. No IT ticket and no admin rights.**

Go to `https://www.python.org/downloads/`. On Windows, the top download is the Python install manager,
checked 2026-09-21. Run it and click Install.

It installs for this person only, in their own user folder. That is why it needs no administrator
password, no IT ticket and no self-service portal, even on a managed work laptop. The Python docs note
one rare exception: Windows may ask for an administrator once, when it needs a system update to its C
runtime. If that happens, go to "When it is blocked".

After it installs the first runtime, it asks whether to add a directory to PATH. Say yes. Then close
and reopen PowerShell, and run `py -3 --version`.

**3. The traditional installer, if the install manager will not run.** On
`https://www.python.org/downloads/windows/`, under a release, is a link named **Windows installer
(64-bit)**. Python deprecated it from 3.14, so it is the fallback. Two things on its first screen matter:

> **Tick "Add python.exe to PATH". Leave every "admin privileges" or "all users" option unticked.**

Then click **Install Now**. With those options off, it installs for this person only and never asks for
an administrator. Missing the PATH checkbox is the most common reason Python seems to install and then
does not work. Running the installer again and choosing **Modify** offers it again.

**4. The Microsoft Store.** Also per user, with no admin rights. Search for **Python** and pick the
**Python install manager** from the Python Software Foundation, or the highest **Python 3.x** package.
Close and reopen PowerShell, then run `py -3 --version` or `python --version`.

**5. winget, last.**

```powershell
winget search Python.Python
```

That lists the available versions. Install the highest `3.x` by the exact id it showed, such as
`winget install Python.Python.3.14`. If winget asks for administrator rights, stop and use step 2,
which never does.

**6. If `python` still does nothing after installing.**

PATH did not get updated. Two ways forward.

```powershell
py -3 --version
```

If that works, use `py -3` everywhere instead of `python`. It is a launcher Windows installs alongside
Python and it is perfectly fine to rely on. Record it in the config and move on.

If that fails too, close every PowerShell window and open a fresh one. PATH changes only apply to new
windows. If it still fails, run the python.org installer again. The install manager offers the PATH
prompt again. The traditional installer offers Repair.

## macOS

**1. Check what is there.**

```bash
python3 --version
```

Printing the minimum `doctor.py` reports or higher means you are done.

**2. If a box appears asking to install developer tools, click Install.**

macOS ships a stub that prompts for the Command Line Tools the first time you ask for `python3`. That
is expected. It downloads a few hundred megabytes and takes a few minutes. When it finishes, run the
version check again.

You can start it deliberately instead:

```bash
xcode-select --install
```

**3. Homebrew, if they already have it.**

```bash
brew install python
```

Do not install Homebrew just for this. The Command Line Tools route is smaller and has fewer moving
parts.

**4. The installer from python.org.**

`https://www.python.org/downloads/macos/`, latest stable, run it, accept the defaults. No checkbox to
worry about on this platform.

## Linux

```bash
python3 --version
sudo apt install python3        # Debian and Ubuntu
sudo dnf install python3        # Fedora and RHEL
```

Almost every desktop Linux already has it.

## Checking it worked

One command, same on every platform apart from the interpreter name.

```bash
python3 -c "import sys; print('Python', '.'.join(map(str, sys.version_info[:3])), 'is working')"
```

On Windows use `python` or `py -3` in place of `python3`, whichever answered earlier.

It has to print the minimum `doctor.py` reports or higher. Anything else means it is not working
yet, whatever the installer said.

## When it is blocked

The install manager from python.org needs no IT ticket, so start there. A ticket is only for a machine
whose policy refuses every installer, including one for this user only. That is not a failure, it is a
ticket. Do not spend an hour working around it.

Give them this to send to their IT team. Ask which channel their workplace uses: a help desk portal,
a ticket queue or an email address. Never guess an address.

```text
Subject: Python 3 install request

I need Python 3 on my work machine to run flarehand, an open-source AI work assistant
(MIT licensed, https://github.com/FlareWare-Solutions/flarehand).

Machine: <from doctor.py>
Preferred: the Python install manager from python.org/downloads, installed for my user only.
It needs no admin rights. Policy on this machine blocked it.
Alternative: the Microsoft Store listing of the Python install manager.

No third-party packages are needed. The tool uses only the Python standard library.
```

That last line matters. It answers the security question before anyone asks it.

## Recording what you found

Once it works, save the interpreter so nothing has to guess again.

```bash
python3 scripts/kb.py init --name "<their name>" --role "<their own words>"
```

This writes the working interpreter path into `config.json`. Everything afterwards reads it from
there, which is why nothing in this skill ever hardcodes `python3`.
