# Wi-Fi: Impala + iwd

Impala là giao diện chọn mạng, iwd là dịch vụ nền. iwd lưu profile/mật khẩu,
tự kết nối và lấy IP bằng DHCP tích hợp; systemd-resolved nhận DNS từ iwd.
Hai gói `impala`, `iwd` thuộc kho Arch chính thức và được cài bằng pacman.
Không cần build ứng dụng Wi-Fi.

## Kết nối và lưu mạng

Nhấn icon Wi-Fi trên Waybar hoặc Utilities → Wi-Fi để mở Impala trong Foot.
Ở console trước khi cài font có thể chạy `impala --ascii`.

1. Chọn Wi-Fi và nhập mật khẩu ở lần kết nối đầu.
2. Mạng đã kết nối được iwd nhớ trong danh sách known networks.
3. Kiểm tra Autoconnect bật; dùng `t` để bật nếu hiện đang tắt. Đừng toggle khi
   nó đã bật. `r` chuyển danh sách trong Impala.
4. Thoát Impala. iwd tiếp tục giữ kết nối và tự kết nối mạng đã lưu khi khả dụng.

`iwd.service` được enable để chạy từ lúc boot, không cần đợi mở Sway/Impala.
Profile của mạng cũ do NetworkManager lưu không tự chuyển sang iwd; chọn lại
mạng và nhập mật khẩu một lần trên Arch mới.

## Cấu hình

`system/etc/iwd/main.conf` cài vào `/etc/iwd/main.conf`:

```ini
[General]
EnableNetworkConfiguration=true

[Network]
NameResolvingService=systemd
```

`/etc/resolv.conf` phải trỏ tới `/run/systemd/resolve/stub-resolv.conf` theo
hướng dẫn cài đặt. Không bật DHCP client hay network manager khác cho cùng
interface Wi-Fi. Cấu hình này phục vụ Wi-Fi; Ethernet/VPN cần được cấu hình
riêng khi có nhu cầu, không có service quản lý chúng được bật sẵn.

Tài khoản thuộc `wheel` theo hướng dẫn cài đặt có quyền dùng iwd qua D-Bus;
không chạy Impala bằng sudo. Giao diện/theme ở `config/impala/config.toml`.

## Kiểm tra sau cài đặt

```bash
systemctl status iwd systemd-resolved
iwctl device list
iwctl known-networks list
iwctl station wlan0 show
resolvectl status
resolvectl query archlinux.org
```

Thay `wlan0` bằng tên thực tế từ `device list`. CLI kết nối dự phòng:

```bash
iwctl station wlan0 connect "TEN_WIFI"
```

Nếu có lỗi, xem `journalctl -b -u iwd -u systemd-resolved`. Sau lần kết nối đầu,
reboot và kiểm tra tự kết nối mà không mở Impala; thử thêm một lần suspend/wake.
Các bước này kiểm chứng phần cứng thật, không thể thay bằng kiểm tra tĩnh.

## Chuyển từ bản dotfiles Arch cũ

Chạy các stage `packages`, `user --backup`, `system --user "$USER" --backup`
theo hướng dẫn rồi reboot. System stage enable iwd và disable các service
NetworkManager/wpa_supplicant đang enabled cho lần boot tiếp theo. Nó không
dừng kết nối đang hoạt động trong lúc cài. Đừng bắt đầu thao tác này qua SSH.
Sau boot, mở Impala/iwctl để lưu lại mạng; profile NetworkManager cũ được giữ
nguyên và không được script chuyển đổi hay xóa.

## Backup mạng đã lưu

Profile/mật khẩu nằm ở `/var/lib/iwd`, thường chỉ root đọc được. Đây là dữ liệu
riêng, không thuộc manifest và không đưa vào Git. Nếu cần mang sang một bản
Arch khác, backup thư mục đó bằng root ra nơi an toàn; restore đúng ownership
và permission khi iwd đã dừng trên máy đích. Không đổi quyền profile để user
thường đọc được. Với nhu cầu đơn giản, nhập lại mật khẩu một lần là đủ.
