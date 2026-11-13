# Chọn bước cài cho PC và laptop

Bạn tự chọn lệnh theo máy. Không có tự nhận diện chassis, hostname hoặc profile
ẩn. Phần ứng dụng và giao diện dùng chung; policy laptop là bước bổ sung.

| Stage | Nội dung |
| --- | --- |
| Bare Git | File cấu hình home tại đúng đường dẫn sử dụng |
| User services | Tùy chọn enable user units và timer bảo trì |
| System | Cấu hình chung: đăng nhập, Wi-Fi, âm thanh, firewall, zram, theme boot |
| Laptop | Giới hạn sạc, lid/sleep và UPower hibernate |

## Máy mới

Cài Arch nền, driver và package trước theo [hướng dẫn cài](installation.md).
Bare Git đưa cấu hình user vào đúng vị trí; sau đó bật user units nếu cần:

```bash
./setup-user-services.sh
sudo ./setup-system.sh system "$USER"
```

**PC:** phần cấu hình hoàn tất ở đây, kiểm tra bằng `./check-health.sh`.

**Laptop:** kiểm tra swap/resume và khả năng hibernate, rồi chạy thêm:

```bash
sudo ./setup-system.sh laptop
./check-health.sh
```

`laptop` chép năm file policy vào `/etc`/`/usr/local`, daemon-reload và enable
`battery-threshold.service` cho boot sau. Không bật ngay ngưỡng sạc,
restart logind/UPower, sleep máy hoặc tạo lại initramfs. Reboot sau khi kiểm tra
để các daemon đọc policy mới. `system` có rebuild initramfs vì cài theme boot.

Không có drop-in `sleep.conf.d/10-laptop.conf`: menu Suspend dùng suspend thường,
idle chỉ khóa/tắt màn hình. Có drop-in: menu và idle dùng policy laptop hiện có.
Đây là kiểm tra cấu hình đã cài, không phải tự chọn loại máy.

## Laptop hiện tại và bộ cài cũ

Năm file giữ nguyên nguồn và đích nên không cần di chuyển hay cài lại hệ.
Chạy `./check-health.sh` để kiểm tra. Nếu cần cập nhật policy, chạy
`sudo ./setup-system.sh laptop` sau khi đọc script và file policy.
Chạy lại stage `system` không gỡ file laptop hoặc disable battery-threshold.

Hai stage cài bổ sung, không phải bộ chuyển profile có chức năng gỡ tự động.
Nếu tái sử dụng một hệ đã cài laptop để làm PC, hãy sao lưu rồi tự xem xét
gỡ năm file policy laptop trong `/etc` và disable `battery-threshold.service`.
Đừng xóa file nào nếu chưa kiểm tra nội dung và quyền sở hữu.

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
