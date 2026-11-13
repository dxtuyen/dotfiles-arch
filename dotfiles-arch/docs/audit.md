# Repository audit, 2026-11-10–11

Historical audit and deployment notes. For the current interface use
[desktop.md](desktop.md); for a clean installation use [installation.md](installation.md).
The backup/restore installer described below was removed on 2026-11-13; conflicts
now stop for manual inspection and handling.
The final shell uses a native Bash prompt; earlier Starship measurements below
describe intermediate configurations.

Scope: installer/manifest, package lists/local recipe, scripts, Sway/Waybar/Foot,
Fcitx, LazyVim, shell, application settings, system and user units, system policy,
bundling and installation/maintenance documentation. Initial Git status contained
one user edit: removal of `makepkg --pkg` in `tools/install.py`. That correction
was retained. No packages were installed/removed; no service was started, stopped,
disabled, restarted or reset; no live file deployment, boot/disk/swap/firmware
change, reboot or destructive Git command was performed.

## Findings and decisions

| Priority | Concrete finding / source | Result |
| --- | --- | --- |
| High | `tools/install.py:aur` passed invalid `makepkg --pkg` before the user's edit | Preserve correction; replace loop with reviewed Paru installs after user approval |
| High | `makepkg --syncdeps` resolves sync-repo dependencies, not AUR-to-AUR dependencies | Delegate resolution of libeb, python-clickgen, providers/version constraints and split packages to Paru |
| High | AUR loop aborted on the first failure; later packages never attempted | Optional `--keep-going` catches per-target errors and returns a final nonzero failure summary |
| High | Original file moved before journal creation in `install_files` | Journal intent and original inode before rename; atomic journal publication with fsync |
| High | Restore consumed backups without recording completion | Record restored items; recover interrupted original-file rename; repeat restore safely |
| High | Restore journal backup path could name unrelated transaction files | Restrict backups to `files/TARGET`, reject traversal, overlaps and symlinked parent escapes |
| Medium | `--cleanbuild` forced source work on every attempted package; no installed-target precheck | Skip installed AUR/local targets; retain helper/build caches and build dependencies |
| Medium | Bibata source builds required clickgen and its dependency chain | Verified upstream checksummed release binary recipe; switch only Bibata to `-bin` |
| Medium | `system_install` silently disabled competing managers | Refuse active/enabled NetworkManager/wpa_supplicant conflicts before file deployment; manual handoff |
| Medium | `config/qt5ct/qt5ct.conf` and Qt6 equivalent referenced a missing palette | Add `share/color-schemes/gruvbox-material.conf`, manifest mapping and reference validation |
| Medium | `bin/session-start` reset every failed user unit at login, hiding unrelated errors | Remove blanket reset; preserve diagnostics |
| Medium | `bin/quick-lang` used predictable response files and exposed API key in curl argv | Private mktemp file, restrictive umask/runtime directory, header supplied through stdin |
| Medium | `.gitignore` excluded `/tests/`; `tools/bundle.py` omitted tests | Ship regression tests in repository and portable bundles |
| Medium | `doctor` stopped at some failed checks and tested iwd/resolved enablement together | Aggregate command failures; test both enablement states individually |
| Medium | Official package command accepted AUR/Flatpak group names | Limit to official groups before pacman invocation; retain full upgrade and prompts |
| Low | Flatpak stage repeatedly asked to install already present app | Check per-user app inventory; skip installed apps; add dry-run |
| Low | Bundle checksum file could overwrite an existing artifact; archive hashing read all bytes | Refuse existing checksum/symlink outputs; stream digest |
| Medium | `docs/installation.md` installed linux-lts and promised an LTS recovery entry | Match the intended single linux kernel, ext4, disk swap and systemd-boot; USB recovery |
| Low | Maintenance claimed two local recipes and described obsolete exact-checkout AUR workflow | Match the one GTK recipe and current Paru review/update behavior |
| Low | Desktop docs named nonexistent wlsunset-run.sh | Correct reference to bin/wlsunset-run |

Line numbers move as fixes land; function names and paths identify the relevant
code. Package evidence is in [packages.md](packages.md).

## Architecture and trade-offs

Keep the existing file manifest and native application configuration. Python's
standard library handles file deployment; pacman handles official packages; Paru
handles AUR resolution/review/build caching. No helper is silently bootstrapped,
no third-party package repository is trusted, and makepkg remains unprivileged.
Paru was approved by the user during this audit. Binary packages still execute
untrusted packaging code and require recipe and provenance review.

Package presence is the retry state. Installer AUR/local stages complete missing
packages; they intentionally skip upgrades of existing versions. Use full pacman
upgrade followed by reviewed `paru -Sua` for maintenance. Rebuilding a changed
local GTK recipe is an explicit manual operation. `--prepare` now previews target
PKGBUILDs; it does not pin or approve a checkout. Review current dependency and
auxiliary files again during build. Paru itself must remain compatible with the
installed libalpm ABI.

Per-target helper calls add some query overhead but isolate independent failures
and reuse installed shared dependencies. `--keep-going` is opt-in; it never turns
failures into success or catches Ctrl+C as a package failure. No custom recursive
resolver or persistent stage-completion database is maintained.

`setup` was evaluated and deferred. Explicit stages expose review, optional
package failures, home replacement and root policy at useful boundaries. See the
short resumable command sequence in packages.md. File recovery covers manifest
replacements; it does not promise rollback of package/script/service side effects.

## Desktop review

The systemd-owned session, Sway-native popup rules, and separation of
iwd/resolved/Impala remain in place. Countdown now uses the official termdown
package in a Foot popup; Waybar has no timer module. Its native idle inhibitor is
a manual toggle. Keep keybindings, Gruvbox appearance, application choices and
hardware policy. The locking services separate idle, pre-sleep lock and
confirmed-lock display behavior.

The three swayidle processes serve different lifecycle events; they are not simply
duplicate autostarts. Do not merge them without testing inhibitor and suspend
ordering. Countdown has no lock/sleep hooks. `keep-awake` uses a process-scoped
systemd sleep inhibitor; `idle-suspend` honors it. Foot/Neovim/LazyVim retain
terminal-first defaults; Mason stays
disabled while language tools come from pacman. Existing Lua/plugin and Yazi locks
are preserved. Global Fcitx/Qt environment changes were deferred to application tests.

## Current machine: read-only observations

All official-list names exist in local sync databases and are installed. Existing
AUR installs include Tofi, Lotus, GoldenDict/libeb, Sioyek and Swayview. Missing AUR
desktop targets are Bibata binary cursors, Gruvbox icons, Brave, Chrome and VS Code;
Paru is not installed. Optional mysql84 is missing. The local GTK assets are absent.
No instruction here requires reinstalling the already successful source builds.

`./install doctor` returned nonzero with 125 failures: most manifest home files
are not deployed, most system files differ/are absent, browsers/themes are missing,
and a user portal unit is failed. This is a deployment/status report, not a claim
that all these are application bugs. iwd and systemd-resolved are enabled. The
non-sandboxed observation showed `/boot` mounted read-write and disk swap active.
No boot/resume or hibernation suitability was inferred from that alone.

The portal journal reports `pipewire: couldn't connect to context` and
`failed to initialize screencast`, followed by start-limit-hit. PipeWire's socket,
service and WirePlumber were inactive when checked, although socket/session-manager
enablement is present. This establishes that the portal could not reach PipeWire;
it does not establish why audio units were inactive. Retry and inspect after the
configured Sway login; do not clear all failures. Read-only follow-up:

```bash
systemctl --user status pipewire.socket pipewire.service wireplumber.service
journalctl --user -b -u pipewire -u wireplumber -u xdg-desktop-portal-wlr
```

## Validation

- `python -m unittest discover -s tests -v`: 32 passing tests. Temporary homes and
  mocked package/privileged operations cover dependency/helper failures, keep-going,
  retry after partial success, Ctrl+C, root refusal, preflight conflict safety,
  atomic backup intent, interrupted install/restore, modified-file refusal,
  directory/symlink originals, path traversal, cross-filesystem failure, seed
  preservation, whole-restore preflight, dry-runs and bundle contents/output safety.
- `python tools/check.py`: passed desktop-file validation, ShellCheck, JSON/TOML/XML
  checks, manifest/executable/Qt palette checks, unit graph/isolated systemd verify,
  headless Sway validation, Foot config check and regressions.
- `ruff check tools tests`: passed; Python syntax compilation and `git diff --check`
  also passed. Broad Ruff inspection found pre-existing import ordering and
  shebang/executable style findings in vocabulary scripts; runtime syntax is valid.
- `./install package-status`: passed official availability checks using local DBs.
- Live AUR RPC plus Bibata binary PKGBUILD inspection: verified names/dependencies
  and Bibata's checksummed upstream release URL. Not a build/signature audit.

Systemd verification initially hit sandbox socket restrictions; the suite was
rerun with permission outside the sandbox. No full installation or AUR/local build
was used as a test. Automated tests prove wrapper/recovery behavior, not Paru's
resolver internals or successful upstream compilation.

## Remaining limits and manual decisions

- Test a real reviewed Paru bootstrap/install and local GTK build on Arch. Upstream
  downloads, recipe quality, keyring state and ABI transitions can still fail.
- Confirm Qt palette rendering in actual Qt5/Qt6 applications. The session selects
  qt6ct globally; legacy Qt5 applications may need a per-app qt5ct environment.
- Hardware/session acceptance remains: lock before sleep, inhibitor ordering,
  suspend/resume/hibernate, Lotus uinput permissions, Wi-Fi autoconnect, audio,
  screen sharing and mixed-output placement. Preserve the existing settings until
  those tests justify changes.
- `system/etc/nftables.conf` uses `flush ruleset`. Reloading it can erase dynamically
  created libvirt/container firewall rules. Do not reload during active guests;
  decide on firewall ownership before changing this policy. It was not applied.
- `apply-longman.py` retains rollback values only in memory; interrupted Anki API
  updates need an Anki collection backup. `configure-goldendict.py` writes app
  preferences outside the manifest journal. Back up application data before these
  workflows; file restore does not roll them back.
- User stage starts existing trash-clean and Flatpak-update timers and adjusts app
  preferences; system stage appends groups and enables services. Review before
  applying; these effects are deliberately outside file rollback.
- Third-party GTK/Qt applications may override appearance. Sioyek-git and bootstrap
  lazy.nvim's stable branch are moving sources; Arch/AUR, Flatpak updates and
  editor ecosystems are not a bit-for-bit system lock. Keep package archives,
  reviewed recipes, plugin lock and external data backups.

Prefer the existing official packages, checksummed vendor release assets where
verified, and AUR source only for the remaining required apps. Avoid extra network,
power-management and compositor daemons. No package removals, kernel/sysctl tuning
or service consolidation were justified by measured evidence in this audit.

## Changed files

- Installer and validation: `tools/install.py`, `tools/check.py`, `tools/bundle.py`,
  `tests/test_install.py`, `tests/test_bundle.py`, `.gitignore`.
- Inventory/appearance: `packages/aur.txt`, `install-manifest.json`,
  `share/color-schemes/gruvbox-material.conf`.
- Session/security: `bin/session-start`, `bin/quick-lang`.
- Documentation: `README.md`, `docs/README.md`, `docs/architecture.md`,
  `docs/desktop.md`, `docs/installation.md`, `docs/maintenance.md`, `docs/wifi.md`,
  `docs/packages.md`, `docs/audit.md`.

Additional integration checks passed: complete manifest installation into a
throwaway offline home, repeat installation, restore dry-run, full restore and
repeat restore; actual portable bundle creation with regression/audit inclusion
and secret/cache exclusions; AUR/local/Flatpak dry-run commands on this machine.

## Live installation follow-up, 2026-11-11

The user subsequently authorized installation and deployment. Home configuration
was deployed with backup `20261110T172050.793523Z`; system files with backup
`20261110T171545.031073Z`. Logind/sleep/zram policy was deliberately excluded.
Keyd was started and validated against the physical ThinkPad keyboard. Sway user
services, Lotus server, PipeWire/WirePlumber and the portal are running.
The missing `sof-firmware` was confirmed by kernel logs and installed with explicit
user approval; reprobe restored speaker and microphone devices without rebooting.
The package hook regenerated the existing linux initramfs; no kernel version,
bootloader entry, disk partition or swap setting was changed.
The GTK build succeeded; its upstream script now receives an isolated HOME.
Neovim plugin restore and headless startup succeeded with the original lockfile.
Read-only diagnostics no longer wait for an installer lock held by a download.
Doctor now reports only the three intentionally preserved hardware-policy files.
A full system upgrade was declined because it also proposed Intel microcode;
no firmware flashing or reboot was performed. The initial icon installation hit a
concurrent pacman lock; its completed package was then installed from cache.

All desktop AUR targets, local GTK theme and TickTick were subsequently confirmed
installed; an AUR rerun skipped every target successfully. Build cleanup removed
about 3.5 GiB while retaining package archives, backups and the edited Sioyek tree.
Bash startup measured roughly 120–160 ms before and 75 ms after direct Fzf script
loading/Starship full initialization; title/OSC7 now emits before prompt setup.
Fzf completion and Ctrl+R/Ctrl+T bindings were verified. Tofi width is now 480 px.
