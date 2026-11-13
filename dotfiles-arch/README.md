# Arch dotfiles

Arch Linux, Sway/Wayland, Gruvbox Material, Foot, Bash, Neovim and Fcitx5-Lotus.
Dotfiles are tracked in place by one bare Git repository at `~/.dotfiles.git`;
`$HOME` is its worktree. There is no home installer or symlink manager.

## Cài máy mới

Sau khi cài Arch và tạo user, clone bare repo vào home:

```bash
git clone --bare git@github.com:dxtuyen/dotfiles-arch.git "$HOME/.dotfiles.git"
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME"'
dotfiles config --local status.showUntrackedFiles no
dotfiles checkout
```

Nếu checkout báo file trùng, kiểm tra rồi tự chuyển file đó đi trước khi chạy lại.
Thêm alias `dotfiles` vào `~/.bashrc` để dùng thường xuyên. Cấu hình mới được
quản lý trực tiếp tại `~/.config`, `~/.local` và các file shell trong home.

Cài package kho chính thức:

```bash
sudo pacman -Syu --needed - < "$HOME/dotfiles-arch/pkglist.txt"
```

AUR và Flatpak được cài riêng theo [ghi chú package](docs/packages.md). Đọc
[hướng dẫn cài Arch](docs/installation.md) trước khi áp cấu hình máy.

## Dùng và bảo trì

```bash
dotfiles status
dotfiles add .config/sway/config
dotfiles commit -m 'Update Sway config'
dotfiles push
```

`~/dotfiles-arch/` giữ package list, cấu hình `/etc`, script setup và tài liệu.
Các file hệ thống không được Git tự chép vào `/etc`: đọc `setup-system.sh` và
chạy riêng khi cần. `setup-user-services.sh` là tùy chọn. Chạy
`./check-health.sh` trong `~/dotfiles-arch` khi cần chẩn đoán.

Xem [kiến trúc](docs/architecture.md), [bảo trì](docs/maintenance.md) và
[cấu hình PC/laptop](docs/hardware.md).
