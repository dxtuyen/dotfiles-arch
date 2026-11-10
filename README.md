# Arch dotfiles

Arch Linux + Sway/Wayland cho laptop Intel: Gruvbox Material Dark, Foot, Bash,
LazyVim và Fcitx5-Lotus. Wi-Fi dùng iwd + Impala + systemd-resolved.
Máy hiện tại dùng một kernel `linux`, systemd-boot, ext4 và swap riêng.

- **Cài mới:** [hướng dẫn từng bước](docs/installation.md).
- **Paru/AUR:** [bootstrap, review và tiếp tục khi lỗi](docs/packages.md).
- **Sử dụng:** [desktop và phím tắt](docs/desktop.md).
- **Bảo trì:** [cập nhật và khôi phục cấu hình](docs/maintenance.md).
- **Tổ chức repo:** [kiến trúc](docs/architecture.md).

Kiểm tra trên máy đã cài:

```bash
./install package-status
./install user --backup --dry-run
python tools/check.py
```

`config/`, `shell/`, `bin/`, `lib/`, `share/`: cấu hình và công cụ người dùng.
`systemd/user/`: service phiên Sway. `system/`: cấu hình hệ thống.
`packages/`: danh sách gói và PKGBUILD local.
`install-manifest.json`: mapping nguồn → đích; `tools/`: bộ cài và kiểm tra.

File người dùng link về checkout, nên giữ nguyên vị trí repo. Stage `system`
chép cả policy swap/ngủ/firewall; đọc hướng dẫn trước khi chạy trên máy đang dùng.
