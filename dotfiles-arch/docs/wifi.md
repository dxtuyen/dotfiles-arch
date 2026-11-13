# Wi-Fi: Impala + iwd + systemd-networkd + systemd-resolved

Impala là giao diện chọn mạng. iwd lưu profile/mật khẩu và tự kết nối Wi-Fi.
systemd-networkd là DHCP client duy nhất, nhận IP, gateway, route và DNS;
systemd-resolved nhận DNS từ networkd và phục vụ phân giải tên.
Hai gói `impala`, `iwd` thuộc kho Arch chính thức và được cài bằng pacman.
networkd/resolved thuộc gói systemd có sẵn; không thêm NetworkManager hay
DHCP client bên ngoài, không cần build ứng dụng Wi-Fi.

## Vì sao đổi DHCP client?

Cấu hình cũ có `EnableNetworkConfiguration=true` và
`NameResolvingService=systemd`. Đây là cú pháp hợp lệ: iwd tự chạy DHCP qua
ELL, nhận DNS rồi chuyển cho resolved. Impala không cấp IP/route; resolved
không tạo IPv4 default route. Không có tùy chọn main.conf còn thiếu để
"bật gateway"; `RoutePriorityOffset` chỉ đổi metric, không sửa gateway bị bỏ qua.

Trên máy đã kiểm tra: iwd 3.12-2 liên kết động với ELL 0.83-1. Mã
[`ell/dhcp-lease.c` bản 0.83](https://kernel.googlesource.com/pub/scm/libs/ell/ell/+/refs/tags/0.83/ell/dhcp-lease.c)
chỉ gán `lease->router` khi DHCP Router option (3) có độ dài **đúng 4 byte**.
Option hợp lệ có nhiều router dài 8, 12… byte bị bỏ qua, trong khi IP và DNS
vẫn được đọc. [RFC 2132 §3.5](https://www.rfc-editor.org/rfc/rfc2132.html#section-3.5)
cho phép danh sách router theo thứ tự ưu tiên. Trong
[`ell/netconfig.c`](https://kernel.googlesource.com/pub/scm/libs/ell/ell/+/refs/tags/0.83/ell/netconfig.c),
gateway rỗng khiến việc tạo default route bị bỏ qua. Đây là một giới hạn
DHCP cụ thể đã xác minh từ mã đúng phiên bản, phù hợp với triệu chứng.

Bảng route thật có subnet `proto dhcp` và default route do người dùng thêm
không có `proto dhcp`. Log iwd báo connected, không ghi chi tiết DHCP options.
Chưa thu được DHCP ACK của mạng trường trong lần kiểm tra này vì đọc phản
hồi DHCP cần quyền root; vì vậy **chưa khẳng định mạng trường gửi nhiều router**.
Để xác nhận nhánh lỗi cụ thể, capture DHCP ACK khi kết nối lại, xem options
3 (router), 1 (mask), 121 (classless routes), rồi đối chiếu route/log.
Không suy gateway từ DNS server, DHCP server hoặc đoán `.1` của subnet.

Lỗi triển khai là repo chỉ giao toàn bộ DHCP cho client này: manifest không
có file `.network`, system stage không enable networkd, hướng dẫn cài mới
cũng bật lại DHCP tích hợp. Đổi file trên máy một lần không sửa các đường
cài lại đó. Nay cả manifest, installer và hướng dẫn chroot đều phân công:
iwd kết nối Wi-Fi; networkd cấu hình IP/route/DNS. Cấu hình dùng DHCP của
từng mạng, không chứa địa chỉ/gateway cố định hoặc script thêm route.

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
EnableNetworkConfiguration=false
```

`system/etc/systemd/network/20-wifi.network` cài vào
`/etc/systemd/network/20-wifi.network`:

```ini
[Match]
Type=wlan
WLANInterfaceType=station

[Network]
DHCP=yes
IPv6AcceptRA=yes

[DHCPv4]
UseRoutes=yes
UseGateway=yes
UseDNS=yes
```

Match theo loại Wi-Fi station, dùng được với `wlan0`, `wlp…` và các SSID
khác nhau; không đụng Ethernet, bridge/VPN hoặc AP/P2P. networkd dùng DHCP
router/classless routes để chọn gateway, cập nhật khi renew hoặc đổi mạng;
DNS lấy từ DHCP/IPv6 RA. `UseRoutes`, `UseGateway`, `UseDNS` được ghi rõ,
đều là hành vi mặc định bật của networkd. Nếu server gửi option 121,
default route phải có trong option đó theo RFC 3442; không tự đoán gateway
khi server không cung cấp. [Manual systemd.network](https://www.freedesktop.org/software/systemd/man/latest/systemd.network.html).

`/etc/resolv.conf` phải trỏ tới `/run/systemd/resolve/stub-resolv.conf` theo
hướng dẫn cài đặt. Không chạy thêm DHCP client cho interface Wi-Fi. File
`.network` khớp đầu tiên được dùng: khi có cấu hình networkd riêng, kiểm tra
`networkctl status` để chắc `20-wifi.network` được chọn. Ethernet/VPN cần
được cấu hình riêng khi có nhu cầu.

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
systemctl is-enabled iwd systemd-networkd systemd-resolved
systemctl is-active iwd systemd-networkd systemd-resolved
iwctl device list
iwctl known-networks list
iwctl station wlan0 show
networkctl status wlan0
ip -4 address show dev wlan0
ip -4 route show dev wlan0
ip -4 route show default
ip -4 route get 1.1.1.1
readlink -f /etc/resolv.conf
resolvectl status wlan0
resolvectl query archlinux.org
curl -4 -I --connect-timeout 10 https://archlinux.org
```

Thay `wlan0` bằng tên thực tế từ `device list`. CLI kết nối dự phòng:

```bash
iwctl station wlan0 connect "TEN_WIFI"
```

Mong đợi `networkctl` chọn `20-wifi.network`, có địa chỉ IPv4 động, default
route `proto dhcp` qua gateway do mạng cung cấp, và DNS trên đúng interface.
`1.1.1.1` chỉ là đích kiểm tra chọn route, không phải gateway/DNS cài đặt.
Kiểm tra này phân biệt route còn thêm tay với route do DHCP quản lý.

Ngắt/kết nối lại trong Impala, chuyển sang hotspot hoặc Wi-Fi khác, rồi kiểm
tra lại: IP/gateway/DNS phải theo mạng mới, không còn gateway của mạng trước.
Thử `sudo networkctl renew wlan0`, suspend/wake và reboot; sau boot tự kết nối
và có route mà không cần mở Impala hoặc chạy `ip route add`. Với mạng có
captive portal, hoàn tất trang đăng nhập sau khi đã có route/DNS.

Nếu có lỗi, xem `journalctl -b -u iwd -u systemd-networkd -u systemd-resolved`.
Các bước này kiểm chứng phần cứng/DHCP thật, không thể thay bằng kiểm tra tĩnh.

## Áp dụng trên máy đang dùng

Từ `~/dotfiles-arch`, đọc file cấu hình và chạy stage system riêng:

```bash
sudo ./setup-system.sh system "$USER"
```

Stage system enable cả ba dịch vụ cho boot sau, **không restart mạng hiện tại**.
Reboot từ console tại máy để áp dụng sạch; hoặc bàn giao ngay tại máy (mạng
ngắt trong chốc lát):

```bash
sudo systemctl stop iwd.service
sudo systemctl enable --now systemd-resolved.service systemd-networkd.service
sudo systemctl start iwd.service
```

Không thực hiện bàn giao qua SSH. Xác nhận `/etc/resolv.conf` như trên;
hướng dẫn cài đặt có lệnh backup và tạo symlink. Profile trong `/var/lib/iwd`
giữ nguyên. File `[IPv4]`/`[IPv6]` tĩnh cũ của iwd không còn quản lý IP khi
network configuration bị tắt; nếu cần IP tĩnh, cấu hình riêng trong networkd.

## Chuyển từ bản dotfiles Arch cũ

System stage từ chối nếu NetworkManager/wpa_supplicant/dhcpcd/ConnMan bản
service toàn cục đang active hoặc enabled;
nó không tự disable service. Lập kế hoạch chuyển quyền quản lý từ console tại máy,
chuẩn bị profile iwd và cách kết nối dự phòng trước khi tự dừng/disable manager cũ.
Không chuyển mạng qua SSH. Sau khi bàn giao xong, chạy lại system stage theo
hướng dẫn. Profile manager cũ được giữ nguyên, không tự chuyển đổi hay xóa.
Kiểm tra thêm các instance như `dhcpcd@wlan0` hoặc `wpa_supplicant@wlan0`
nếu từng tự bật; các instance này cũng không được tranh quyền quản lý Wi-Fi.

## Backup mạng đã lưu

Profile/mật khẩu nằm ở `/var/lib/iwd`, thường chỉ root đọc được. Đây là dữ liệu
riêng, không đưa vào Git. Nếu cần mang sang một bản
Arch khác, backup thư mục đó bằng root ra nơi an toàn; restore đúng ownership
và permission khi iwd đã dừng trên máy đích. Không đổi quyền profile để user
thường đọc được. Với nhu cầu đơn giản, nhập lại mật khẩu một lần là đủ.
