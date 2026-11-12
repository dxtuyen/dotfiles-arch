# Arch dotfiles

Arch Linux + Sway/Wayland: Gruvbox Material Dark, Foot, Bash,
LazyVim và Fcitx5-Lotus. Wi-Fi dùng iwd + Impala + systemd-resolved.
Máy hiện tại là laptop Intel, dùng một kernel `linux`, systemd-boot, ext4 và swap riêng.

- **Cài mới:** [hướng dẫn từng bước](docs/installation.md).
- **Paru/AUR:** [bootstrap, review và tiếp tục khi lỗi](docs/packages.md).
- **Sử dụng:** [desktop và phím tắt](docs/desktop.md).
- **Bảo trì:** [cập nhật và khôi phục cấu hình](docs/maintenance.md).
- **Tổ chức repo:** [kiến trúc](docs/architecture.md).
- **PC/laptop:** [chọn bước cài hệ thống](docs/hardware.md).

Cài app theo một lượt sau khi đã bootstrap Paru:
`./install apps --unattended --keep-going` (xem trước bằng `--dry-run`).
Lệnh gom kho chính thức + AUR qua Paru, rồi theme local/Flatpak; cấu hình
`user`/`system` vẫn áp dụng riêng. Xem [hành vi tự động](docs/packages.md).

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

File người dùng link về checkout, nên giữ nguyên vị trí repo. Bạn tự chọn bước
cài theo máy, bộ cài không dò PC/laptop:

```bash
# Chung cho PC và laptop, sau khi cài gói và user stage
sudo ./install system --user "$USER" --backup

# Laptop: chạy thêm
sudo ./install laptop --backup
./install doctor --laptop

# PC: kiểm tra phần chung
./install doctor
```

Xem trước mỗi lệnh cài bằng `--dry-run`. `system` vẫn chép firewall/zram và
tạo lại initramfs với theme Plymouth. `laptop` chỉ bổ sung pin/lid/sleep;
chạy lại `system` giữ nguyên policy laptop đã cài. Driver, boot và swap/resume
cần cấu hình theo máy; danh sách gói hiện vẫn theo máy Intel đang dùng.
