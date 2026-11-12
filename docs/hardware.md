# Chọn bước cài cho PC và laptop

Bạn tự chọn lệnh theo máy. Không có tự nhận diện chassis, hostname hoặc profile
ẩn. Phần ứng dụng và giao diện dùng chung; policy laptop là bước bổ sung.

| Stage | Nội dung |
| --- | --- |
| `user` | File home, Sway, Waybar, shell, tiện ích và user service |
| `system` | Cấu hình chung: đăng nhập, mạng Wi-Fi, âm thanh, firewall, zram, theme boot và dịch vụ |
| `laptop` | Giới hạn sạc 85–90%, lid undocked suspend-then-hibernate, sleep và UPower hibernate ở pin 10% |

## Máy mới

Cài Arch nền, driver và các gói trước theo [hướng dẫn cài](installation.md).
Trong checkout, chạy bằng user thường; chỉ hai stage root dùng sudo:

```bash
./install user --backup --dry-run
./install user --backup
sudo ./install system --user "$USER" --backup --dry-run
sudo ./install system --user "$USER" --backup
```

**PC:** phần cấu hình hoàn tất ở đây, kiểm tra bằng `./install doctor`.

**Laptop:** kiểm tra swap/resume và khả năng hibernate, rồi chạy thêm:

```bash
sudo ./install laptop --backup --dry-run
sudo ./install laptop --backup
./install doctor --laptop
```

`laptop` chỉ chép năm file trong nhóm `laptop` của manifest, daemon-reload và
enable `battery-threshold.service` cho boot sau. Không bật ngay ngưỡng sạc,
restart logind/UPower, sleep máy hoặc tạo lại initramfs. Reboot sau khi kiểm tra
để các daemon đọc policy mới. `system` có rebuild initramfs vì cài theme boot.

Không có drop-in `sleep.conf.d/10-laptop.conf`: menu Suspend dùng suspend thường,
idle chỉ khóa/tắt màn hình. Có drop-in: menu và idle dùng policy laptop hiện có.
Đây là kiểm tra cấu hình đã cài, không phải tự chọn loại máy.

## Laptop hiện tại và bộ cài cũ

Năm file giữ nguyên nguồn và đích nên không cần di chuyển hay cài lại hệ.
Chạy `./install doctor --laptop` để kiểm tra. Nếu cần cập nhật policy, chỉ chạy
`sudo ./install laptop --backup --dry-run`, xem diff rồi bỏ `--dry-run`.
Chạy lại stage `system` không gỡ file laptop hoặc disable battery-threshold.

Hai stage cài bổ sung, không phải bộ chuyển profile có chức năng gỡ tự động.
Nếu tái sử dụng một hệ đã cài laptop để làm PC, bỏ qua stage laptop chưa gỡ
policy cũ. Xem journal trong `/var/lib/dotfiles/backups/`, chọn đúng transaction
đã cài laptop và dùng `sudo ./install restore DUONG_DAN_TRANSACTION --dry-run`
trước khi restore; không restore cả transaction chung của bộ cài cũ chỉ để gỡ pin.
Restore không hoàn tác enable service: cần disable `battery-threshold.service`
và kiểm tra lại từng file cũ khi thực sự bỏ policy laptop. Backup trước và reboot
sau khi hoàn tất; không xóa hàng loạt `/etc` hoặc các file đã tự sửa.

## Phần cứng vẫn cần cấu hình theo máy

Tách stage pin/ngủ không tự chọn driver hoặc cài bootloader. Danh sách gói và
ví dụ boot hiện theo laptop Intel: PC AMD/NVIDIA cần chọn microcode, driver GPU
và initramfs phù hợp. PC dùng Ethernet cần cấu hình mạng cho interface của nó;
repo hiện quản lý Wi-Fi bằng iwd. Zram dùng chung; swap đĩa/resume cho hibernate
là phần thiết lập riêng, không được stage laptop tự tạo.

Phím độ sáng dùng `brightnessctl` cho backlight, không điều khiển màn hình rời
bằng DDC/CI. Menu power profile hiện có ba lựa chọn theo laptop đang dùng;
máy thiếu profile sẽ báo lỗi khi chọn, cần chỉnh theo hỗ trợ thực tế của máy đó.
Waybar và cấu hình âm thanh được giữ nguyên trong lần tách stage này.
