# Wi-Fi sau khi cài Arch

iwd lưu profile và kết nối Wi-Fi. systemd-networkd cấp IP, route và DNS qua DHCP cho card ở chế độ station. systemd-resolved phân giải tên. Cấu hình nguồn nằm ở [main.conf](../system/etc/iwd/main.conf) và [20-wifi.network](../system/etc/systemd/network/20-wifi.network).

## Kiểm tra kết nối

Chạy `iwctl device list` để tìm tên card, rồi thay `wlan0` trong các lệnh bên dưới.

```bash
iwctl station wlan0 show
networkctl status wlan0
ip -4 route show default
resolvectl status wlan0
resolvectl query archlinux.org
```

Kiểm tra lần lượt tên mạng đã kết nối, file `20-wifi.network` đang áp dụng, default route của DHCP và kết quả truy vấn DNS. Dùng `journalctl -b -u iwd -u systemd-networkd -u systemd-resolved` để đối chiếu thời điểm mất kết nối.

## Áp dụng trên máy đang dùng

Stage `system` enable các dịch vụ cho boot sau. Khi chuyển từ trình quản lý mạng khác, thao tác tại console, chuẩn bị profile iwd và dừng trình quản lý cũ trước khi áp dụng cấu hình. Sau khi reboot, kiểm tra `/etc/resolv.conf` trỏ tới `/run/systemd/resolve/stub-resolv.conf`. Các bước cài đầy đủ ở [hướng dẫn từ USB](installation.md).

Profile chứa thông tin đăng nhập ở `/var/lib/iwd`. Có thể nhập lại mật khẩu trên máy mới. Nếu phục hồi từ backup, chép khi iwd đang dừng và giữ quyền sở hữu cùng quyền truy cập gốc.

## Ca thiếu default route trước đây

Trước khi chuyển DHCP sang networkd, máy từng nhận IP và DNS nhưng thiếu default route. ELL 0.83 chỉ đọc DHCP Router option dài 4 byte. Đây là một nguyên nhân có thể giải thích triệu chứng. Lần đó chưa thu DHCP ACK của mạng trường để xác nhận. [Mã xử lý lease của ELL 0.83](https://kernel.googlesource.com/pub/scm/libs/ell/ell/+/refs/tags/0.83/ell/dhcp-lease.c).
