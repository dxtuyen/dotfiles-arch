# Desktop

`Super` là phím Windows/logo. Toàn bộ keybinding/rule nằm ở
`config/sway/config`.

Màn boot dùng Plymouth với nền Gruvbox `#282828` và spinner có sẵn của gói
`plymouth`. Theme ở `share/plymouth/gruvbox-material/`; thay theme xong cần
chép file hệ thống tương ứng và chạy `sudo mkinitcpio -P`.

Tuigreet trên VT1 dùng 16 màu từ `system/etc/greetd/vtrgb`, khớp bảng ANSI của
Foot. Drop-in `greetd.service.d/10-console.conf` nạp bảng này bằng `setvtrgb`
trước khi greetd khởi động. Chỉnh vai trò màu ở `system/etc/greetd/config.toml`.
`--remember` lưu username đăng nhập thành công trong `/var/cache/tuigreet/lastuser`;
thư mục và file phải thuộc `greeter:greeter`. Người dùng vẫn nhập mật khẩu.
File `share/color-schemes/gruvbox-material.conf` là palette dành riêng cho Qt.

| Phím | Hành vi |
| --- | --- |
| Super+Enter / Super+D | Foot / Tofi launcher |
| Super+O / Super+I / Super+G | Popup Obsidian / TickTick / GoldenDict |
| Super+grave | Popup terminal |
| Alt+Tab | Quay lại workspace vừa dùng; nhấn tiếp đổi giữa hai workspace |
| Super+Tab | Overview workspace bằng swayview |
| Super+1…9,0 | Workspace 1–10; thêm Shift để chuyển cửa sổ |
| Super+H/J/K/L hoặc mũi tên | Focus; thêm Shift để di chuyển cửa sổ |
| Super+[ / Super+] | Workspace trước/sau; thêm Shift để chuyển cửa sổ |
| Super+B/V; Super+S/W/E | Split ngang/dọc; stacking/tabbed/toggle split |
| Super+F / Super+Shift+Space | Fullscreen / floating |
| Super+- / Super+Shift+- | Hiện scratchpad / đưa cửa sổ vào scratchpad |
| Super+R | Chế độ resize; Enter/Esc thoát |
| Super+C | Countdown |
| Super+U / Super+P | Utilities / power menu |
| Super+Esc | Khóa màn hình |
| Super+Shift+C | Reload Sway và khôi phục chế độ màu màn hình |
| Super+Shift+E | Hỏi thoát Sway |
| Print / Alt+Print | Copy vùng chọn / toàn màn hình |
| Shift+Print / Ctrl+Print | Lưu vùng chọn / toàn màn hình, đồng thời copy |
| Super+Print | Menu screenshot |
| Super+T / Super+Shift+T / Super+Ctrl+T | Dịch sang Anh / Việt / sửa tiếng Anh |
| Super+Alt+T | Bật/tắt touchpad |

## Popup và menu

Sway sở hữu geometry, focus và scratchpad; helper chỉ quyết định launch/toggle,
không tự dựng lại window manager bằng Python. Popup đang hiện nhưng chưa focus
sẽ được focus trước; nhấn tiếp mới ẩn. Đóng/mở lại cửa sổ sau khi đổi window
rule để rule gắn mark mới. Obsidian 70%×85%, TickTick 60%×75% ở lần mở đầu.

Tofi dùng phím mũi tên hoặc Ctrl+J/K, Enter chọn, Esc hủy. Launcher lưu history;
menu tiện ích không lưu. Tofi không có icon ảnh hoặc chọn chuột; các biểu tượng
menu là font glyph. Độ rộng mặc định 480 px. Helper giữ đúng action gốc khi lọc/reorder menu.
Waybar đã bỏ nút nguồn; mở menu nguồn bằng `Super+P`.
Workspace không ghim sẵn số; Waybar chỉ hiện các workspace đang tồn tại.

## Giao diện

Foot dùng JetBrainsMono Nerd Font cỡ 11. Prompt Bash hai dòng: đường dẫn xanh
Gruvbox, dấu `❯` xanh lá và một dòng trống ngăn với kết quả lệnh; không gọi
Starship hoặc quét Git mỗi prompt. Mở Foot mới sau khi sửa font hoặc shell.
Foot mở trong thư mục được truyền từ nơi gọi; `nt` giữ thư mục đang làm việc.

Desktop dùng `desktop.png`; màn hình khóa dùng `lock.png`, logo Arch nhỏ phía
trên. Vòng khóa nhỏ, không hiện thường trực; sáng rõ khi nhập mật khẩu.
Sửa giao diện khóa có hiệu lực ở lần khóa mới, không cần restart swaylock.

## Session và Countdown

- Không hoạt động: màn hình tắt sau 5 phút, khóa sau 10 phút.
- Không hoạt động 15 phút: suspend-then-hibernate khi dùng pin. Trên AC tiếp tục
  khóa/tắt màn hình, kiểm tra lại nguồn mỗi 30 giây sau deadline.
- Khóa thủ công: sau 10 giây không input thì tắt màn hình. Input bật lại để mở khóa.
- Countdown đang chạy hoặc keep-awake giữ **idle inhibitor**; explicit lock,
  menu Suspend và lid vẫn hoạt động.
- Khóa thành công hoặc chuẩn bị sleep: Countdown pause, giữ thời gian còn lại,
  xóa keep-awake thủ công. Mở khóa/wake không tự resume timer.
- Khi áp dụng policy system của repo: lid undocked ngủ cả khi cắm sạc; docked
  thì bỏ qua. Sau một giờ suspend,
  systemd chuyển sang hibernate theo khả năng phần cứng.

Deadline ở `systemd/user/swayidle.service`; timeout locked ở
`locked-display.service`; timer kiểm tra nguồn ở `idle-suspend.timer`.
Lid/hibernate delay ở `system/etc/systemd/`. Khi chỉnh, giữ screen-off < lock < sleep.
Chạy kiểm tra rồi áp dụng file system nếu đã đổi; reboot để logind dùng cấu hình mới.

Countdown worker theo dõi state bằng inotify. Waybar chỉ render state và nhận
signal; không điều khiển service trong mỗi lượt render. Lịch sử ở
`~/.local/state/countdown-history.log`; state runtime reset khi kết thúc login
session. Khôi phục history không đồng nghĩa khôi phục timer đang chạy.

## Media, mạng và màn hình

Volume thay 5%, giới hạn 0–100%; giảm đến 0 thì mute, tăng từ 0 về 5% và unmute.
Mic/speaker mute mỗi lần nhấn một lần. Brightness thay 10%, tối thiểu 5%.
WireMix/Bluetui/Impala chạy trong Foot. Nhấn trái/phải icon Wi-Fi hoặc chọn
Utilities → Wi-Fi đều mở Impala. iwd lưu mạng, cấp IP và tự kết nối lại; DNS
do systemd-resolved xử lý. Đóng Impala không làm mất kết nối.

Lần đầu chọn Wi-Fi và nhập mật khẩu. Trong danh sách mạng đã biết, kiểm tra
Autoconnect đã bật; phím `t` đổi trạng thái này. `r` đổi giữa các danh sách,
`s` bật/tắt quét, `o` bật/tắt thiết bị, Esc thoát. Mật khẩu/profile được lưu
riêng ở `/var/lib/iwd`, không cần mở Impala mỗi lần boot. Dòng chọn dùng nền
`#45403d` để phân biệt với nền Foot. Xem [quản lý Wi-Fi](wifi.md).

Night light dùng `wlsunset@MODE.service`, chỉ lưu lựa chọn sau khi service đã
khởi động thành công. Menu đọc trạng thái service; preference ở
`~/.local/state/wlsunset-mode`. Tọa độ mặc định Hà Nội trong `bin/wlsunset-run`.

## Ứng dụng và dữ liệu

PDF mặc định mở Sioyek; F8 đổi page color. Yazi giữ default opener ở Enter,
Shift+O chọn ứng dụng cho lần mở đó. Đổi default browser trong browser; lựa
chọn ở `~/.config/mimeapps.list` không bị bộ cài ghi đè.

Trong Bash, `y` mở Yazi rồi chuyển shell đến thư mục cuối; `nt` mở Foot hoặc
tmux window ở thư mục hiện tại. Keyd: Caps tap → Esc, hold → Ctrl; hai Shift → CapsLock.
Fzf, zoxide và direnv vẫn hoạt động cùng prompt Bash thuần.

Quick Lang đọc selection/clipboard, gửi văn bản đến Gemini và copy kết quả.
Key ở `~/.config/quick-lang/api.key`, mode 600, không lưu trong Git.
GoldenDict dùng `~/Dictionary/Longman`; helper `goldendict-anki-config` giữ
cấu hình kết nối Anki. Sync collection trước khi chạy `anki-longman-setup`.
AnkiConnect cần được cài và cho phép kết nối local như tài liệu trong
`lib/vocabulary/assets/anki/README.md`.
