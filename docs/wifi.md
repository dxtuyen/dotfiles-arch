# Wi-Fi: Impala + iwd

Impala là giao diện chọn mạng, iwd là dịch vụ nền. iwd lưu profile/mật khẩu,
tự kết nối và lấy IP bằng DHCP tích hợp; systemd-resolved nhận DNS từ iwd.
Hai gói `impala`, `iwd` thuộc kho Arch chính thức và được cài bằng pacman.
Không cần build ứng dụng Wi-Fi.

## Kết nối và lưu mạng

Nhấn icon Wi-Fi trên Waybar hoặc Utilities → Wi-Fi để mở Impala trong Foot.
Foot và Impala chạy bằng tài khoản thường. Repo không cấp theme hay phím tắt
riêng cho Impala; dùng mặc định của ứng dụng, nhấn `q` để thoát.
Ở console trước khi cài font có thể chạy `impala --ascii`.

1. Chọn Wi-Fi và nhập mật khẩu ở lần kết nối đầu.
2. Mạng đã kết nối được iwd nhớ trong danh sách known networks.
3. Kiểm tra Autoconnect bật; dùng `t` để bật nếu hiện đang tắt. Đừng toggle khi
   nó đã bật. `Tab` chuyển giữa các vùng/danh sách trong Impala.
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
chạy `impala` trực tiếp bằng tài khoản thường vẫn đủ để kết nối/quét mạng.
Riêng Share (`p`) trong Impala 0.9.0 đọc `Passphrase` trực tiếp từ profile
`/var/lib/iwd/*.psk`. Khi cần chia sẻ, mở Foot rồi chạy `sudo impala`; xác thực
sudo khi được hỏi, chọn mạng đã lưu và nhấn `p`. Profile cần có `Passphrase`
đã lưu; root không bổ sung khả năng chia sẻ cho mọi loại mạng. Thoát bằng `q`
sau khi dùng. Không có quy tắc sudoers riêng để miễn mật khẩu cho Impala.

Phím mặc định: `s` quét một lượt, `Tab` chuyển vùng, mũi tên chọn mạng,
`Enter` kết nối/ngắt kết nối. Impala 0.9.0 chưa có ô gõ tên để lọc mạng.

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

System stage từ chối nếu NetworkManager/wpa_supplicant đang active hoặc enabled;
nó không tự disable service. Lập kế hoạch chuyển quyền quản lý từ console tại máy,
chuẩn bị profile iwd và cách kết nối dự phòng trước khi tự dừng/disable manager cũ.
Không chuyển mạng qua SSH. Sau khi bàn giao xong, chạy lại system stage theo
hướng dẫn. Profile manager cũ được giữ nguyên, không tự chuyển đổi hay xóa.

## Backup mạng đã lưu

Profile/mật khẩu nằm ở `/var/lib/iwd`, thường chỉ root đọc được. Đây là dữ liệu
riêng, không thuộc manifest và không đưa vào Git. Nếu cần mang sang một bản
Arch khác, backup thư mục đó bằng root ra nơi an toàn; restore đúng ownership
và permission khi iwd đã dừng trên máy đích. Không đổi quyền profile để user
thường đọc được. Với nhu cầu đơn giản, nhập lại mật khẩu một lần là đủ.
