# Kiến trúc

Repo là nguồn cấu hình của laptop Arch: quản lý file, dependency và service.
Dữ liệu và trạng thái ứng dụng nằm ngoài repo. Ứng dụng đọc cấu hình gốc;
không có framework sinh cấu hình hoặc theme chạy nền.

## Tổ chức theo đường dẫn sử dụng

Cây nguồn phản chiếu các vị trí chuẩn của Unix/XDG. Mở `config/sway/config`
là thấy file Sway thực sự đọc; không qua cây module hay file sinh trung gian.

| Nguồn | Nơi dùng | Nội dung |
| --- | --- | --- |
| `config/APP/` | `~/.config/APP/` | Cấu hình gốc của ứng dụng |
| `bin/TEN_LENH` | `~/.local/bin/TEN_LENH` | Command gọi từ shell/keybinding |
| `lib/` | `~/.local/lib/dotfiles/` theo manifest | Helper nội bộ, workflow/assets |
| `share/` | `~/.local/share/` | Wallpaper, desktop entry, dữ liệu theme |
| `shell/` | Bash startup/helper trong home | Code phải chạy trong shell gọi nó |
| `systemd/user/` | `~/.config/systemd/user/` | Unit gốc, cùng tên với journalctl |
| `system/etc/` | `/etc/` | Policy máy, chỉ stage root được ghi |
| `system/bin/` | `/usr/local/bin/` | Helper hệ thống, chép file thường |

Command đơn giản có một file trong `bin/`, không thêm wrapper chỉ để đổi tên
hoặc nhét đường dẫn dependency vào PATH. Python/assets của workflow từ điển ở
`lib/vocabulary/`; code và tài nguyên phải đi cùng nhau để helper tự tìm được
asset theo vị trí của nó. Helper Tofi ở `lib/tofi-menu.sh`; các menu dùng chung
API trình bày, mỗi command giữ logic hành động của mình.

Unit được đặt tập trung theo namespace systemd. `swayidle.service` và
`countdown-engine.service` tìm trực tiếp theo tên, không phải đoán chúng thuộc
một thư mục module nào. Phần config không chứa logic enable service ẩn.

Thêm thành phần theo nhu cầu thực: file cấu hình trong `config/`, command trong
`bin/`, unit trong `systemd/user/`, dependency vào nhóm package tương ứng.
Không tạo thêm tầng `desktop/programs/features`, module enable/import, hoặc
file template khi cấu hình gốc đã đáp ứng. Giữ code phức tạp cùng assets trong
`lib/TEN_WORKFLOW/`, tránh biến `lib/` thành thư mục chứa đồ không rõ mục đích.

## Nguồn và nơi cài

`install-manifest.json` ghi rõ từng nguồn, đích, chế độ. Thêm thành phần cần thêm
vào manifest và package list; kiểm tra phát hiện nguồn thiếu, target trùng/chồng
và command không executable. Không tự đoán file cần bật bằng `find` lúc cài.

| Chế độ | Hành vi |
| --- | --- |
| `link` | Liên kết nguồn trong repo; ứng dụng đọc lại khi reload |
| `seed` | Chép lần đầu; giữ thay đổi Fcitx qua GUI |
| `render` | Chép cấu hình Qt, thay duy nhất `@@HOME@@` bằng home thực tế |
| `copy` | Chép file hệ thống; root service không chạy qua symlink về home |

`~/.config/mimeapps.list` thuộc người dùng/ứng dụng. Repo cấp mặc định ưu tiên
thấp hơn ở `~/.local/share/applications/mimeapps.list`. Neovim giữ plugin lock
trong checkout; plugin nằm ngoài repo. Theme GTK riêng là gói pacman có phiên
bản. Impala/iwd dùng binary từ kho chính thức.

Wi-Fi có một nơi quản lý: iwd sở hữu kết nối, profile lưu và IP/DHCP;
systemd-resolved xử lý DNS. Impala chỉ là giao diện, không phải daemon cần
autostart. Cấu hình hiện tại dành cho Wi-Fi; không bật thêm networkd hoặc
NetworkManager cùng quản lý interface đó. Profile/mật khẩu ở `/var/lib/iwd`,
không ở trong repo.

Giữ nguyên đường dẫn checkout sau khi link. Nếu move repo, chạy lại stage
`user --backup` từ chỗ mới. Bộ cài tự tìm checkout và home của người dùng.

## Stage và quyền

- `apps`: một transaction Paru cho kho chính thức + AUR, rồi tái sử dụng stage
  theme local và Flatpak. `--unattended` chấp nhận mặc định công cụ và bỏ review
  trong lượt đó; Paru sở hữu sudo-loop, không có daemon hay policy sudo riêng.
  Đây là luồng cài/nâng cấp gói, không tự áp file `user`/`system`.

- `packages`: full upgrade và gói chính thức qua pacman.
- `aur --build`: Paru giải quyết dependency và review recipe trước khi build;
  makepkg chạy bằng user, pacman nâng quyền khi cài gói/dependency.
  `--prepare` chỉ xem trước PKGBUILD chính, không ghim revision.
- `local-packages`: build PKGBUILD ghim commit/checksum trong repo.
- `flatpak`: TickTick ở phạm vi user.
- `user`: file home, enable user unit; không đụng bootloader/phân vùng.
- `system`: chép `/etc`, helper `/usr/local/bin`, theme Plymouth, tạo lại
  initramfs và enable service cho lần boot sau; không restart mạng/login manager.
- `doctor`: kiểm tra trên Arch; không tự sửa hoặc sleep máy.

Boot, partition, UUID swap và tài khoản có bước riêng trong hướng dẫn.
MySQL server tùy chọn vì build nguồn tốn thời gian. Stage `system` vẫn gồm policy
zram/lid/sleep; chưa tách thành stage phần cứng riêng. Đọc plan trước khi chạy lại.

Shell dùng prompt Bash thuần, giữ Fzf/zoxide/direnv. Starship không còn được
khởi tạo hoặc yêu cầu trong package list; file theme cũ được giữ để tham khảo.

## Cài lại và khôi phục

Kiểm tra toàn bộ xung đột trước khi thay file. Mặc định dừng nếu đích có nội dung
ngoài quản lý. `--backup` chuyển bản cũ vào transaction có journal, sau đó thay
file bằng rename. Chạy lại khi nguồn/đích khớp không tạo backup mới.
Backup user: `~/.local/state/dotfiles/backups/`; root: `/var/lib/dotfiles/backups/`.

`./install restore PATH_TRANSACTION` khôi phục một lần cài file. Kiểm tra cả
transaction trước khi làm, từ chối xóa file đã sửa sau cài. Không rollback gói,
dữ liệu hoặc phân vùng. Nếu bị ngắt, dữ liệu cũ/journal giữ lại để khôi phục.

## Vòng đời session

Tuigreet gọi wrapper hệ thống, rồi `~/.local/bin/dotfiles-sway` của user. Sway
chạy trực tiếp trong login session. Sau khi Wayland/IPC sẵn sàng, `session-start`
xuất môi trường sang D-Bus/systemd rồi start `sway-session.target`. Wrapper dừng
target khi compositor thoát. Service con do systemd giám sát; không autostart
trùng qua `.bashrc`, XDG và Sway.

Khóa thành công mới kích hoạt `session-locked.target`. Countdown đăng ký target
để pause; session không gọi thẳng Countdown. Countdown giữ logind idle inhibitor
theo process, theo dõi state bằng inotify. Worker cập nhật đồng hồ khi chạy;
Waybar nhận tín hiệu thay vì poll.

## Tối ưu có thể kiểm chứng

Ưu tiên kho chính thức, chỉ giữ gói/service cần dùng và dùng cơ chế sẵn có của
Sway/systemd. Không thêm kernel tùy biến, governor daemon thứ hai, sysctl chưa
đo hiệu quả hay tự động update toàn hệ thống.

Tham khảo mô hình symlink theo thành phần của
[GNU Stow](https://www.gnu.org/software/stow/manual/) và tách nguồn/đích của
[chezmoi](https://www.chezmoi.io/reference/concepts/). Dùng Python chuẩn cho
các yêu cầu file root, mutable file và pacman; không cần cài hai công cụ đó.

## Kiểm tra

`python tools/check.py` kiểm tra inventory, TOML/JSON/XML, ShellCheck, desktop
entry, unit graph gồm `.wants`, kiểm tra headless bằng Sway/Foot.
Test hành vi ở `tests/`, được quản lý trong Git và đưa vào bundle.
Chạy riêng bằng `python -m unittest discover -s tests -v`.
Không có CI bắt buộc. Input, âm thanh, portal,
bộ gõ, suspend/hibernate thật vẫn phải kiểm tra trên laptop.
