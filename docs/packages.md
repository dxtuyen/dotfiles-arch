# Packages, review and recovery

Run these commands as the normal login user. This is the installation procedure;
the historical audit/deployment record is in [audit.md](audit.md). Read Arch news before upgrading.
Do not run `pacman -Sy` alone, bypass dependency checks, disable signature checks,
or use `--noconfirm`. AUR recipes are arbitrary code, including binary recipes.

## Sources

Official lists (`base`, `desktop`, `apps`, `development`, `virtualisation`) go
through `sudo pacman -Syu --needed`. All their names were found in this machine's
sync databases during the audit. `./install package-status` checks again without
refreshing databases or changing packages. `packages --dry-run` prints the command.

Live [AUR RPC metadata](https://aur.archlinux.org/rpc/v5/info?arg[]=goldendict-ng&arg[]=libeb&arg[]=bibata-cursor-theme&arg[]=bibata-cursor-theme-bin&arg[]=python-clickgen&arg[]=sioyek&arg[]=sioyek-git&arg[]=paru-bin)
was checked on 2026-11-10:

| Target | Decision |
| --- | --- |
| goldendict-ng | AUR source; depends on AUR libeb, which makepkg cannot fetch itself |
| bibata-cursor-theme | Source recipe requires AUR python-clickgen>=2.0.0 |
| bibata-cursor-theme-bin | Use checksummed Bibata upstream release assets; avoids cursor generation |
| sioyek-git | Keep existing choice; `sioyek` absent from queried AUR and local official DBs |
| brave-bin, google-chrome, visual-studio-code-bin | Existing vendor binaries repackaged by AUR recipes |
| tofi, fcitx5-lotus, swayview, gruvbox-plus-icon-theme | Keep verified existing AUR names |
| mysql84 | Optional source build, outside the desktop list |
| paru-bin | Verified bootstrap option using upstream precompiled release |

Bibata binary recipe was also inspected: its archive comes from
`github.com/ful1e5/Bibata_Cursor/releases` with a SHA-256 checksum, and it provides
and conflicts with `bibata-cursor-theme`. Pacman may ask to replace an existing
source variant; review that prompt. Binary packaging avoids compilation but still
requires trusting both the upstream publisher and the reviewed packaging code.
No third-party binary repository or signing key is added.

## Bootstrap Paru once

Paru was selected instead of maintaining a custom resolver for versioned deps,
providers, split packages, build order and review. It is itself unofficial.
See [upstream](https://github.com/Morganamilo/paru) and its
[manual](https://github.com/Morganamilo/paru/blob/master/man/paru.8).

First finish `./install packages` (full upgrade, normal pacman prompts). Then:

```bash
# A fresh temporary directory avoids overwriting any existing clone.
PARU_REVIEW_DIR=$(mktemp -d /tmp/dotfiles-paru-review.XXXXXXXX)
git clone https://aur.archlinux.org/paru-bin.git "$PARU_REVIEW_DIR/paru-bin"
cd "$PARU_REVIEW_DIR/paru-bin"
git log -1 --oneline
less PKGBUILD .SRCINFO
# Inspect any other tracked files, download URLs, checksums/signatures and arch support.
git ls-files
# ONLY after approving the recipe; run as your normal user:
makepkg --syncdeps --install --needed
cd ~/dotfiles-arch
```

Do not run makepkg as root. Do not source a PKGBUILD just to inspect it. Keep
installation prompts enabled. If no suitable upstream binary exists for your
architecture, review/bootstrap `paru` from AUR instead; it needs a Rust build.
When pacman changes libalpm ABI, Paru may need a compatible release/rebuild.

## Complete a partial installation

```bash
cd ~/dotfiles-arch
./install package-status
./install packages --dry-run
./install packages
# Bootstrap Paru above if `command -v paru` fails.
./install aur --build --dry-run
./install aur --build --keep-going
./install local-packages --dry-run
./install local-packages
./install flatpak --dry-run
./install flatpak
./install user --backup --dry-run
```

Read each review screen, including AUR dependencies, `.install` files and patches.
`--review` is passed explicitly; no automatic acceptance is used.
`--noremovemake` retains build dependencies, avoiding automatic removals and
repeated downloads. Each independent AUR target gets a separate helper invocation
so `--keep-going` can continue after a failure. Shared dependencies are reused.
Without `--keep-going`, stop at the first failure. Both modes exit nonzero on any
failure, retaining the helper's original diagnostics on the terminal.

`--prepare` is optional and now prints target PKGBUILDs using `paru -Gp`.
It does **not** approve or pin them. Build fetches/reviews the current recipes
and their dependencies. Old `~/.cache/dotfiles/build/` checkouts are left intact;
Paru uses its own cache. Preserve local recipe edits there before migrating them.

Rerun the same stage after fixing a failure. Installed AUR/local/Flatpak targets
are skipped; no stage-success file can incorrectly hide a missing package. AUR
updates are separate: full official upgrade, then `paru -Sua --review --noremovemake`.
To deliberately rebuild an installed target, use Paru directly after review.
The local GTK installer also skips installed versions; use a reviewed manual
`makepkg -si` for a changed local recipe. AUR/devel sources and rolling Arch are
not fully reproducible; retain package archives and `pacman -Q` inventory for recovery.

After inspecting the file plan and differences against current files:

```bash
./install user --backup
sudo ./install system --user "$USER" --backup --dry-run
# Review system/etc and diff it against /etc before the next command.
sudo ./install system --user "$USER" --backup
./install doctor
```

These apply configuration, enable services and start the user maintenance timers;
run them only when ready. The system stage refuses competing network managers,
never disables them, and does not restart networking or the login manager.
It copies laptop policy including zram, lid/sleep and firewall settings: review
these explicitly for the machine. It does not edit partitions, boot entries,
kernel command lines, swap partitions, firmware or accounts' existing data.
On an existing machine, do not rerun the system stage merely to apply UI changes.
There is currently no hardware-policy opt-out flag. If you intentionally keep
logind/sleep/zram policy different from the repo, doctor reports those differences.
Do not reboot until boot/resume/DNS have been checked using installation.md.

## File recovery

Transaction paths are printed during file installation. Existing files require
`--backup`; seed files preserve GUI edits. File replacements are atomic, but the
whole stage is not one transaction. Restore does not undo package installs,
gsettings, app preference helpers, group membership or service enablement.

```bash
./install restore "$HOME/.local/state/dotfiles/backups/ACTUAL_TIMESTAMP" --dry-run
./install restore "$HOME/.local/state/dotfiles/backups/ACTUAL_TIMESTAMP"
```

Use `sudo` only for a root-owned `/var/lib/dotfiles/backups/ACTUAL_TIMESTAMP`
transaction. Restore preflights every target and refuses to discard edited
replacements or unknown temporary files. Move such files aside after inspecting
them, then retry. Journal writes precede original-file moves and are published
atomically with fsync. Restore records completed items and can be rerun after an
interruption. If a backup rename crosses filesystems, the installer stops rather
than falling back to a potentially incomplete copy; the original remains intact.
Keep these backups until the installation is validated.

Independent stages are intentional. A `setup` command was evaluated but deferred:
a single command would mix package review, optional failures, home replacement and
root service policy. The sequence above is easier to inspect and resume.
