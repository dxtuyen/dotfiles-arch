# Desktop

`Super` là phím Windows/logo. Toàn bộ keybinding/rule nằm ở
`config/sway/config`.

Màn boot dùng Plymouth với nền Gruvbox `#282828` và spinner có sẵn của gói
`plymouth`. Theme ở `share/plymouth/gruvbox-material/`; logo Arch được căn riêng
bằng `WatermarkHorizontalAlignment`/`WatermarkVerticalAlignment`. Khi cài mới,
stage `system` chép theme và tự tạo lại initramfs; làm theo
[hướng dẫn cài đặt](installation.md#9-áp-dụng-cấu-hình), không cần script sửa riêng.
Nếu máy đang dùng chỉ đổi theme, chép file theme tương ứng rồi chạy
`sudo mkinitcpio -P`, không cần áp dụng lại toàn bộ policy hệ thống.

Hướng dẫn boot dùng `fbcon=nodefer` để console nhận framebuffer sớm, tránh đổi
kích thước lúc tuigreet bắt đầu vẽ. Hiệu quả cần kiểm tra trên máy thực sau
reboot; xem [tài liệu fbcon](https://docs.kernel.org/fb/fbcon.html).

Tuigreet trên VT1 dùng 16 màu từ `system/etc/greetd/vtrgb`, khớp bảng ANSI của
Foot. Drop-in `greetd.service.d/10-console.conf` nạp bảng này bằng `setvtrgb`
trước khi greetd khởi động. Chỉnh vai trò màu ở `system/etc/greetd/config.toml`.
`--remember` lưu username đăng nhập thành công trong `/var/cache/tuigreet/lastuser`;
gói `greetd-tuigreet` cung cấp tmpfiles để tạo thư mục cache thuộc
`greeter:greeter`. Trên máy mới nhập username lần đầu, sau lần đăng nhập thành
công tuigreet tự nhớ; không cần tạo hoặc chép `lastuser` từ máy cũ. Người dùng
vẫn nhập mật khẩu.
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
| Super+Z | Danh sách scratchpad; chọn cửa sổ để gọi ra |
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

## Workspace

Workspace có tên số `1`, `2`, `3`, `10`. Waybar chỉ ghim ba
workspace đầu và hiện số + icon: sách mở, code, lưới ứng dụng. Anki dùng icon hai
thẻ chồng nhau với số `0`, hiện trên thanh khi workspace tồn tại.
Workspace trống dùng màu muted (`grey1 #928374` của Gruvbox Material), cùng
Bluetooth tắt/idle; workspace đang chọn và workspace có thông báo khẩn vẫn nổi bật.
Study dành cho giáo trình, NotebookLM và AI hỗ trợ học; Dev dành
cho terminal, code, máy ảo và AI hỗ trợ thực hành; Misc dành cho web, email,
nhắn tin, lịch gia sư, mạng xã hội và các việc riêng khác.
Anki tự mở ở workspace 10 (`Super+0`). Obsidian vẫn là popup dùng được từ mọi workspace.
Trình duyệt và AI có thể mở ở cả Study lẫn Dev tùy công việc.
`Super+số` chọn workspace; thêm Shift để chuyển cửa sổ. Các workspace 4–9
vẫn dùng theo số và hiện trên thanh khi tồn tại.

## Popup và menu

`Super+Z` hoặc bấm biểu tượng scratchpad trên Waybar mở danh sách tiêu đề cửa sổ
đang ẩn, có đánh số bằng Tofi, không hiện app ID. Menu rộng 720 px, nhãn `S ❯`; các menu khác
giữ kích thước mặc định. Gõ để lọc, Enter gọi cửa sổ về workspace hiện tại, Esc hủy.
Cửa sổ đã lấy ra không còn trong danh sách; ẩn lại thì trở về ở lần mở menu sau.
Chọn theo container ID nên tiêu đề trùng
không gọi nhầm cửa sổ. Sau khi chọn, `Super+Q` đóng cửa sổ như bình thường.
Popup terminal `Super+grave` có nhãn `T · ~/thư-mục` trong menu để dễ nhận ra.
Menu chỉ chạy khi được gọi, không có daemon hay polling. App ẩn trong scratchpad
vẫn chạy; menu không tự tạm ngưng ứng dụng.

Sway sở hữu geometry, focus và scratchpad; helper chỉ quyết định launch/toggle,
không tự dựng lại window manager bằng Python. Popup đang hiện nhưng chưa focus
sẽ được focus trước; nhấn tiếp mới ẩn. Đóng/mở lại cửa sổ sau khi đổi window
rule để rule gắn mark mới. Obsidian 70%×85%, TickTick 60%×75% ở lần mở đầu.

Mark của Sway là duy nhất cho một cửa sổ. Cửa sổ chọn vault Obsidian hoặc cửa
sổ phụ TickTick có thể lấy mark rồi mang nó mất khi đóng. Nếu mark không còn,
`obsidian-toggle` và `ticktick-toggle` nhờ Sway tìm lại cửa sổ theo app_id/class,
gắn lại mark rồi toggle; chỉ launch
khi không còn cửa sổ phù hợp. Helper dùng command IPC, không giữ PID hoặc đọc
cây cửa sổ. Lỗi IPC ngoài trường hợp không có cửa sổ vẫn được báo và dừng.

Tofi dùng phím mũi tên hoặc Ctrl+J/K, Enter chọn, Esc hủy. Launcher lưu history;
menu tiện ích không lưu. Tofi không có icon ảnh hoặc chọn chuột; các biểu tượng
menu là font glyph. Độ rộng mặc định 480 px. Helper giữ đúng action gốc khi lọc/reorder menu.
Waybar đã bỏ nút nguồn; mở menu nguồn bằng `Super+P`.
Waybar ghim workspace 1–2–3; các workspace khác chỉ hiện khi đang tồn tại.
Sway và Waybar dùng cùng định danh số `1`, `2`, `3`, `10`; Study/Dev/Misc/Anki
được thể hiện bằng icon trên thanh. Không trộn tên `1.Study` với `1`: nút
ghim của Waybar chọn theo tên chính xác, còn `workspace number 1` của Sway
có thể tìm workspace theo số. Hai tên khác nhau có thể tạo hai workspace
cùng số. Bấm lại workspace đang chọn không tự chuyển về workspace trước.

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
- Sau stage `laptop`, không hoạt động 15 phút: suspend-then-hibernate khi dùng pin. Trên AC tiếp tục
  khóa/tắt màn hình, kiểm tra lại nguồn mỗi 30 giây sau deadline.
- Khóa thủ công: sau 10 giây không input thì tắt màn hình. Input bật lại để mở khóa.
- Countdown đang chạy hoặc keep-awake giữ **idle inhibitor**; explicit lock,
  menu Suspend và lid vẫn hoạt động.
- Khóa thành công hoặc chuẩn bị sleep: Countdown pause, giữ thời gian còn lại,
  xóa keep-awake thủ công. Mở khóa/wake không tự resume timer.
- Sau khi mở khóa, Mako nhắc một lần nếu Countdown đang pause và còn thời gian,
  kể cả timer đã pause thủ công. Không gửi lời nhắc lúc khóa hoặc vừa wake.
- Khi áp dụng stage `laptop`: lid undocked ngủ cả khi cắm sạc; docked
  thì bỏ qua. Không đặt deadline hibernate theo thời gian khóa hoặc thời gian ngủ.
- Đang thức và dùng pin: Waybar gửi cảnh báo Mako khi vào mức 15% hoặc thấp hơn;
  UPower tự hibernate ở 10%, kể cả khi đang có idle inhibitor.
- Đang suspend-then-hibernate: systemd dùng cơ chế pin yếu (dưới khoảng 5%) để
  chuyển sang hibernate, tùy hỗ trợ đánh thức của phần cứng. Không dùng mốc một giờ.

Deadline ở `systemd/user/swayidle.service`; timeout locked ở
`locked-display.service`; timer kiểm tra nguồn ở `idle-suspend.timer`.
Chỉ cài stage chung: idle giữ khóa/tắt màn hình, không tự ngủ theo policy laptop;
menu Suspend dùng `suspend`. Sau stage laptop (có drop-in sleep), menu dùng
`suspend-then-hibernate`. Hành vi này giữ nguyên trên laptop đã cài bằng bộ cài cũ.
Lid/sleep ở `system/etc/systemd/`; ngưỡng pin ở
`system/etc/UPower/UPower.conf.d/60-laptop.conf`, cảnh báo ở `config/waybar/config`.
Khi chỉnh, giữ screen-off < lock < sleep. Chạy kiểm tra rồi áp dụng file system
nếu đã đổi; reload logind và restart UPower, hoặc reboot, để dùng policy mới.
Laptop mới cần thiết lập swap/resume và thử hibernate rồi khôi phục phiên thành
công trước khi dựa vào bảo vệ pin tự động; xem `docs/installation.md`.

Countdown worker theo dõi state bằng inotify. Waybar chỉ render state và nhận
signal; không điều khiển service trong mỗi lượt render. Lịch sử ở
`~/.local/state/countdown-history.log`; state runtime reset khi kết thúc login
session. Khôi phục history không đồng nghĩa khôi phục timer đang chạy.
Engine chỉ gửi tín hiệu tới đúng process Waybar của cùng user đã cài handler
cho tín hiệu đó (`pkill --require-handler --exact --euid`). Nhờ vậy, tín hiệu
cập nhật lúc vào phiên không làm Waybar thoát trước khi sẵn sàng nhận.

## Media, mạng và màn hình

Phím volume thay 5 điểm phần trăm cho mọi đầu ra (loa và tai nghe Bluetooth),
giới hạn 0–100%. Giảm đến 0 thì mute; tăng từ 0 về 5% và unmute.
Tăng khi đang mute ở mức khác 0 chỉ
khôi phục mức đó, không tăng thêm.
Mic/speaker mute mỗi lần nhấn một lần. Brightness thay 10%, tối thiểu 5%.
Nút Play/Pause, Pause, Stop, Next/Previous (kể cả nút tai nghe Bluetooth phát
sự kiện AVRCP) gọi `playerctl` qua MPRIS; ứng dụng cần hỗ trợ media session.
Đã tắt đồng bộ âm lượng phần cứng Bluetooth nên nút volume của tai nghe có thể
chỉnh mức riêng, độc lập thanh âm lượng máy; chức năng phát/tạm dừng vẫn riêng biệt.
EW47 đã thử đồng bộ nhưng âm lượng quá lớn nên giữ chế độ phần mềm,
với bước chỉnh 5 điểm phần trăm trên máy. Sau khi chuyển từ đồng bộ sang riêng,
mức âm lượng phần cứng của tai nghe phải khác 0; tăng phần mềm không thể bù
cho phần cứng đang ở 0. Mức nghe được nhớ riêng theo thiết bị, không cân bằng
độ lớn của tai nghe và loa theo cùng một phần trăm.
WireMix/Bluetui/Impala chạy trong Foot. Nhấn trái/phải icon Wi-Fi hoặc chọn
Utilities → Wi-Fi đều mở Impala. iwd lưu mạng và tự kết nối lại;
systemd-networkd cấp IP/route qua DHCP, chuyển DNS cho systemd-resolved.
Đóng Impala không làm mất kết nối.

Lần đầu chọn Wi-Fi và nhập mật khẩu. Trong danh sách mạng đã biết, kiểm tra
Autoconnect đã bật; phím `t` đổi trạng thái này. `Tab` chuyển vùng/danh sách,
`s` quét một lượt, `o` bật/tắt thiết bị, `q` thoát. Mật khẩu/profile được lưu
riêng ở `/var/lib/iwd`, không cần mở Impala mỗi lần boot. Impala dùng màu và
phím mặc định, chạy bằng user thường; chỉ khi cần Share mới tự mở
`sudo impala` trong Foot. Xem [quản lý Wi-Fi](wifi.md).

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
GoldenDict trên máy mới không có đường dẫn từ điển và tắt các nguồn online/demo;
bạn tự thêm dictionary sau. Helper `goldendict-anki-config` giữ giao diện và kết
nối Anki; `anki-longman-setup --check` kiểm tra mà không ghi dữ liệu. Quy trình
restore/sync, cài AnkiConnect và thêm thẻ bằng một lần bấm ở
[GoldenDict → Anki](vocabulary.md).
