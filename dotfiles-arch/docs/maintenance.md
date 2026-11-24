# Bảo trì

Đọc [Arch News](https://archlinux.org/news/) trước khi nâng cấp. Kiểm tra ESP đang mount tại `/boot` để kernel và initramfs được ghi vào đúng nơi.

```bash
findmnt /boot
sudo pacman -Syu
paru -Sua --review
flatpak update --user
```

Sau khi nâng cấp, xem các file `.pacnew` bằng `pacdiff`. Nếu ứng dụng AUR báo thiếu thư viện sau full upgrade, kiểm tra gói cần build lại bằng `checkrebuild`. Xem [ghi chú package](packages.md).

## Kiểm tra khi có lỗi

```bash
~/dotfiles-arch/check-health.sh
systemctl --failed
systemctl --user --failed
```

Đọc log đúng dịch vụ và lần boot, ví dụ `journalctl -b -u greetd` hoặc `journalctl --user -b -u waybar`. Với lỗi khởi động, dùng [hướng dẫn cứu từ USB](installation.md#11-nếu-không-vào-được-desktop).

## Dữ liệu cần sao lưu

Git giữ phiên bản của những file đã track. Sao lưu riêng từ điển, collection Anki, khóa SSH, dữ liệu ứng dụng và máy ảo. File trong `~/dotfiles-arch/system/` là bản nguồn. Khi cập nhật policy, so với file ở `/etc` và sao lưu các chỉnh sửa riêng trước khi áp dụng.
