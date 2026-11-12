# Packages, review and recovery

Run these commands as the normal login user. This is the installation procedure;
the historical audit/deployment record is in [audit.md](audit.md). Read Arch news before upgrading.
Do not run `pacman -Sy` alone, bypass dependency checks or disable signature checks.
The normal stages retain review. The explicit `apps --unattended` mode below
skips review and accepts package-tool defaults for this run, as requested.
AUR recipes are arbitrary code, including binary recipes.

## One command for the package stages

After bootstrapping Paru once, preview and then choose one mode:

```bash
./install apps --unattended --keep-going --dry-run
./install apps --unattended --keep-going
```

Run as the normal login user, without `sudo` on the installer. Paru requests
sudo authentication when needed and keeps it refreshed with its own `--sudoloop`
during long work. With ordinary cached-credential policy this avoids repeated
expiry prompts; special sudo policies or a new session may still authenticate.
There is no sudoers change or installer-owned background password loop.

The main transaction is one `paru -Syu` for the selected official groups plus
`aur.txt`: full official/AUR upgrade, deduplicated targets, `--needed`,
`--batchinstall`, retained make dependencies and normal dependency/signature
checks. Existing foreign packages may therefore be upgraded too, unlike the
missing-only legacy `aur --build` stage. `--keep-going` lets Paru try independent
AUR builds; a nonzero main transaction stops the later stages and stays nonzero.

Then the existing local-theme stage packages missing recipes using `paru -Bi`
with the same sudo-loop/automatic mode, and Flatpak installs missing user apps
with its native noninteractive options. `mysql84` is not added by this command;
it remains the optional `aur-database` group. Home/system file deployment,
service configuration, boot policy, dictionary data and Anki collection setup
remain separate.

`--unattended` passes `--skipreview --noconfirm` to Paru. This is appropriate only
when you accept the configured package/recipe sources without reviewing them
during that run. Unexpected dependency/signature/conflict failures are errors,
not a reason to disable checks or report success. Run `./install apps` for the
interactive one-transaction workflow with recipe review instead. Individual
stages below remain useful for targeted retries and manual control.

Keep the terminal/session running. If needed, use the desktop's existing
keep-awake mode while waiting; unattended does not mean detached or immune to
suspend/network failure. No actual update is performed by `--dry-run`.

## Sources

Official lists (`base`, `desktop`, `apps`, `development`, `virtualisation`) go
through `sudo pacman -Syu --needed`. All their names were found in this machine's
sync databases during the audit. `./install package-status` checks again without
refreshing databases or changing packages. `packages --dry-run` prints the command.

Prefer official repository binaries, then upstream binaries packaged through AUR.
Keep source builds when no suitable binary package is available. AUR's `--build`
stage also packages downloaded binaries; it does not always compile software.

Live [AUR RPC metadata](https://aur.archlinux.org/rpc/v5/info?arg[]=tofi&arg[]=tofi-bin&arg[]=goldendict-ng&arg[]=goldendict-ng-appimage&arg[]=fcitx5-lotus-bin&arg[]=sioyek-git&arg[]=sioyek-appimage&arg[]=swayview-bin)
and the binary recipes were checked on 2026-11-11:

| Target | Decision |
| --- | --- |
| goldendict-ng | Keep current native source package (26.11.0); AUR AppImage recipe is outdated (23.09.29); libeb also builds from AUR |
| bibata-cursor-theme | Source recipe requires AUR python-clickgen>=2.0.0 |
| bibata-cursor-theme-bin | Use checksummed Bibata upstream release assets; avoids cursor generation |
| sioyek-git | Keep native development source package; stable AppImage 2.0.0 is older than the installed version |
| fcitx5-lotus-bin | Checksummed upstream Arch Linux binaries; keeps the Lotus server service |
| swayview-bin | Checksummed upstream executable; avoids a Rust build |
| brave-bin, visual-studio-code-bin | Existing vendor binaries repackaged by AUR recipes |
| tofi | Source build retained; no tofi-bin found in AUR |
| gruvbox-plus-icon-theme | Copy upstream icon assets; no application compilation |
| mysql84 | Optional source build, outside the desktop list |
| paru-bin | Verified bootstrap option using upstream precompiled release |

Bibata binary recipe was also inspected: its archive comes from
`github.com/ful1e5/Bibata_Cursor/releases` with a SHA-256 checksum, and it provides
and conflicts with `bibata-cursor-theme`. Pacman may ask to replace an existing
source variant; review that prompt. Binary packaging avoids compilation but still
requires trusting both the upstream publisher and the reviewed packaging code.
No third-party binary repository or signing key is added.

On an existing machine, the next `./install aur --build` offers to replace
`fcitx5-lotus` and `swayview` with their binary variants through normal package
conflict prompts. Do not uninstall them first. Already installed Tofi,
GoldenDict and Sioyek are skipped; they are not rebuilt on every installer run.

Sioyek stays on `sioyek-git` to retain the newer native version and avoid
downgrading configuration or databases to the stable 2.0.0 AppImage. No AppImage
runtime is added. Source builds remain for Tofi, GoldenDict/libeb and Sioyek;
the local GTK recipe only generates theme CSS.

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

The build stage also passes `--sudoloop`: Paru periodically refreshes cached sudo
credentials while it is running, so a long build is less likely to require
another password before package installation. This is Paru's own mechanism, not
a permanent change to sudoers. The first authentication, a new terminal/session,
or a policy requiring fresh authentication may still prompt. Build steps remain
unprivileged. Recipe review and pacman's installation/conflict confirmations
are separate from password prompts and remain interactive. `--prepare` only reads
recipes and does not start a sudo loop.

Without `--keep-going`, stop at the first failure. Both modes exit nonzero on any
failure, retaining the helper's original diagnostics on the terminal.

`--prepare` is optional and now prints target PKGBUILDs using `paru -Gp`.
It does **not** approve or pin them. Build fetches/reviews the current recipes
and their dependencies. Old `~/.cache/dotfiles/build/` checkouts are left intact;
Paru uses its own cache. Preserve local recipe edits there before migrating them.

Rerun the same stage after fixing a failure. Installed AUR/local/Flatpak targets
are skipped; no stage-success file can incorrectly hide a missing package. AUR
updates are separate: full official upgrade, then
`paru -Sua --review --noremovemake --sudoloop`.
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
# Laptop only, after checking swap/resume:
sudo ./install laptop --backup --dry-run
sudo ./install laptop --backup
./install doctor --laptop
# PC: skip laptop and use the common check instead:
./install doctor
```

These apply configuration, enable services and start the user maintenance timers;
run them only when ready. The system stage refuses competing network managers,
never disables them, and does not restart networking or the login manager.
It rebuilds initramfs after copying the Plymouth theme; a failed build stops
the stage and must be resolved before rebooting.
It copies common zram and firewall settings. The separate, explicitly selected
`laptop` stage copies battery, lid/sleep policy and the charge-threshold helper;
it only reloads systemd and enables the battery service for the next boot.
See [PC/laptop installation](hardware.md). Neither stage edits partitions, boot entries,
kernel command lines, swap partitions, firmware or accounts' existing data.
On an existing machine, do not rerun the system stage merely to apply UI changes.
The common stage preserves any laptop policy already installed. `doctor` checks
common files; `doctor --laptop` includes laptop files and battery-service enablement.
If you intentionally keep a selected stage's policy different, doctor reports it.
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

The `apps` entry point groups package work only. File deployment stays in the
independent `user`/`system` stages so package automation does not implicitly
replace home files or apply hardware/boot policy.
