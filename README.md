# Arch dotfiles

Môi trường Arch Linux thuần cho laptop Intel: Sway/Wayland, Gruvbox Material,
Foot, Bash, LazyVim, Fcitx5-Lotus và các workflow học tập hiện tại.
Repo độc lập với `~/dotfiles` của NixOS; không cần Nix hay Home Manager.
Wi-Fi dùng Impala + iwd; iwd lưu mạng, tự kết nối và cấp IP, systemd-resolved xử lý DNS.
Impala/iwd cài binary từ kho chính thức, không cần build riêng.

**Cài lại từ USB:** đọc [hướng dẫn từ A đến Z](docs/installation.md).
Dành cho UEFI, SSD hiện tại, ext4 và swap riêng, không mã hóa.
Sao lưu dữ liệu và repo Arch này ra thiết bị khác trước khi format SSD.
Phần tạo remote/commit/push do bạn thực hiện. Sau khi push lên repo public
`dxtuyen/dotfiles-arch`, máy mới có thể clone qua HTTPS; repo NixOS cũ vẫn riêng.

Sau khi đã có Arch và đăng nhập bằng tài khoản thường:

```bash
cd ~/dotfiles-arch
./install packages
./install aur --prepare
# Đọc PKGBUILD, .install và patch trong ~/.cache/dotfiles/build/.
./install aur --build
./install local-packages
./install flatpak
./install user --backup --dry-run
./install user --backup
sudo ./install system --user "$USER" --backup
```

Kiểm tra DNS, boot/resume và làm các bước cuối trong hướng dẫn trước khi reboot.
`./install doctor` kiểm tra dependency và cấu hình trên Arch.
Kiểm tra repo bằng `python tools/check.py`.

```text
config/           Cấu hình ứng dụng, cùng tên/định dạng như trong ~/.config
bin/              Lệnh người dùng, cài vào ~/.local/bin
lib/              Helper dùng chung; workflow lớn có code/assets riêng
share/            Wallpaper, desktop entry, màu Qt, theme Fcitx
shell/            Bash startup và shell function
systemd/user/     User service/target/timer, tên file đúng như systemd
system/
  etc/            Cấu hình root, cài vào /etc
  bin/            Helper hệ thống, cài vào /usr/local/bin
packages/         Danh sách pacman/AUR/Flatpak và PKGBUILD local
install           Điểm vào bộ cài
install-manifest.json  Mapping nguồn → đích và chế độ cài
tools/            Bộ cài, kiểm tra, tạo bundle
docs/             Cài đặt, kiến trúc, desktop, bảo trì, khôi phục
```

Xem [kiến trúc](docs/architecture.md), [desktop](docs/desktop.md) và
[bảo trì](docs/maintenance.md). Cấu hình link về checkout; giữ nguyên thư mục
repo sau khi cài.
