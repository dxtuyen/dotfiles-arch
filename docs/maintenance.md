# Bảo trì và khôi phục

## Cập nhật

```bash
cd ~/dotfiles-arch
git status
sudo pacman -Syu
```

Đọc [Arch news](https://archlinux.org/news/) trước đợt nâng cấp lớn. Không dùng
`pacman -Sy TEN_GOI` vì tạo partial upgrade. Máy dùng một kernel `linux`. Kiểm tra ESP được
mount khi update kernel; chạy `sudo bootctl update` khi cần cập nhật bootloader.
Reboot sau update kernel/systemd rồi kiểm tra service lỗi.

AUR không tự update. Installer chỉ hoàn tất gói còn thiếu, không nâng cấp gói
đã cài. Sau full upgrade chính thức, cập nhật AUR và review recipe/dependency:

```bash
paru -Sua --review --noremovemake --sudoloop
```

Xem [package workflow](packages.md). Paru cache recipe/build; không ép cleanbuild.
`--sudoloop` dùng cơ chế sẵn có của Paru để gia hạn xác thực sudo trong lúc build
lâu. Nó giảm việc hỏi lại do timeout; lần đầu hoặc policy riêng vẫn có thể hỏi.
Các câu hỏi review recipe, thay gói và xác nhận cài là bước khác, vẫn giữ nguyên.
Các source `-git` vẫn có thể thay đổi theo upstream. Arch/AUR không cung cấp khóa
toàn hệ thống như Nix. Một gói local GTK ghim commit/checksum; khi đổi recipe,
review rồi build thủ công từ thư mục cache hoặc checkout với `makepkg -si` bằng
user thường. Installer bỏ qua gói local đã cài, kể cả khi recipe repo đã đổi.

Flatpak tự cập nhật daily qua timer user, độc lập gói pacman. Chạy thủ công:

```bash
flatpak update --user
systemctl --user list-timers
```

Không tự động nâng cấp toàn hệ thống bằng timer.

## Giữ hệ thống sạch và tránh xung đột thư viện

Mỗi file hệ thống cần có chủ sở hữu qua pacman. Ưu tiên kho chính thức; ứng dụng
thiếu mới dùng AUR. PKGBUILD local cũng tạo gói để pacman quản lý. Không chép
thư viện thủ công vào `/usr/lib`, không `sudo make install`, không dùng
`--overwrite '*'` để vượt qua file conflict. Dùng `pacman -Qo DUONG_DAN_FILE`
để tìm chủ sở hữu và xử lý nguyên nhân xung đột.

Sau full upgrade, xem `.pacnew`/`.pacsave` và thay đổi AUR:

```bash
sudo DIFFPROG='nvim -d' pacdiff
pacman -Qm
sudo pacman -Dk
checkrebuild
```

`checkrebuild` từ `rebuild-detector` giúp phát hiện gói cần rebuild sau khi thư
viện đổi SONAME. Đây là công cụ phát hiện, không thay thế việc đọc lỗi/log.
Các gói AUR biên dịch như Tofi/GoldenDict-ng/Sioyek có thể cần rebuild sau update Qt,
Python hoặc thư viện tương ứng. Không ghim phiên bản thư viện nền bằng
`IgnorePkg` để giữ một ứng dụng cũ; update/rebuild app hoặc chạy môi trường cũ
trong container. `pacman -Qdt` liệt kê orphan để **xem xét**, không tự xóa cả
danh sách khi chưa biết package nào bạn vẫn dùng.

Python của hệ thống thuộc pacman. Mỗi project dùng `.venv`:

```bash
cd /DUONG_DAN_PROJECT
uv venv
uv pip install -r requirements.txt
```

Python CLI ngoài pacman dùng `pipx` hoặc `uv tool`; không cài cùng một CLI bằng
cả hai. Không `sudo pip` hoặc `--break-system-packages`. Node dependency nằm
trong project với lockfile, dùng `npm ci`; không cần `sudo npm install -g`.
Project cần distro/thư viện cũ dùng Podman/Distrobox. Các công cụ LSP của desktop
được pacman quản lý; Mason tắt để tránh executable trùng tên trong PATH.

Brave dùng **một bản** `brave-bin` native. Không cài thêm bản Flatpak để cùng
quản lý profile. AUR binary vẫn là gói pacman; kiểm tra recipe khi cập nhật.
Native không cung cấp isolation thư viện ngang Flatpak/container, nên vẫn cần
full upgrade và dependency đúng. TickTick dùng Flatpak vì phù hợp nguồn phân phối.

Lotus và Swayview dùng `fcitx5-lotus-bin`/`swayview-bin`. Cập nhật bằng Paru
như các gói AUR khác, không cần biên dịch hai ứng dụng này.
Nếu binary native lỗi sau khi thư viện đổi ABI,
kiểm tra bản binary upstream mới thay vì ép rebuild recipe chỉ đóng gói binary.
Tofi, GoldenDict-ng và Sioyek còn build từ nguồn: Tofi chưa có binary tương ứng,
recipe AppImage của GoldenDict-ng đang cũ, còn Sioyek AppImage stable 2.0.0
cũ hơn bản `sioyek-git` hiện dùng. Bộ cài bỏ qua các gói đã cài.
Theme GTK local chỉ tạo CSS cho biến thể Dark Medium;
Gruvbox icons chỉ chép asset. Không đổi sang build toàn bộ ứng dụng để cài theme.

## Đổi cấu hình

Sửa file gốc trong repo, chạy `python tools/check.py`, reload ứng dụng tương ứng.
Với symlink, không cần chạy bộ cài để thay nội dung. Thêm file/đổi manifest thì
chạy `./install user --backup --dry-run`, xem kết quả rồi `./install user --backup`.
Sửa file system: xem dry-run trước khi chạy lại stage `system --backup`
cho cấu hình chung (gồm zram/firewall), hoặc `laptop --backup` cho pin/lid/sleep.
Chỉ áp dụng sau khi đã review các file thuộc stage đó. PC kiểm tra bằng
`./install doctor`; laptop dùng `./install doctor --laptop`.
Stage chung giữ nguyên file laptop đã cài; xem [chọn phần cứng](hardware.md)
khi chuyển từ bộ cài cũ hoặc tái sử dụng hệ đã có policy laptop.
Chạy `systemctl --user daemon-reload` khi đổi unit; logout/login để test vòng đời
session, tránh restart riêng lock service khi đang thao tác. Waybar reload bằng
`systemctl --user reload waybar.service`; Foot/Tofi/Impala đọc cấu hình khi mở mới.
Swaylock đọc giao diện ở lần khóa tiếp theo.

Giữ plugin lock của Neovim trong Git sau khi review. Seed Fcitx không tự ghi đè
setting qua GUI. Muốn reset một seed, backup file đó rồi xóa riêng nó trước khi
chạy lại user stage. Không xóa cả `.config`.

## Zram và swap đĩa

Policy trong `system/etc/systemd/zram-generator.conf`: zram bằng nửa RAM,
nén zstd, priority 100. Swap đĩa priority 10 ở ví dụ cài đặt vẫn giữ cho
overflow và ảnh hibernate. Dung lượng zram là dung lượng logic, không phải
RAM bị giữ sẵn ngay khi bật.

Khi bật zram, đặt `zswap.enabled=0` trong dòng `options` của boot entry đang dùng
(ví dụ systemd-boot: `/boot/loader/entries/arch.conf`). Giữ nguyên UUID root/resume
và các tham số khác. Bước boot này làm riêng theo máy; installer không tự sửa entry.
Không cần rebuild initramfs chỉ vì đổi dòng options của entry systemd-boot này.

Máy đã cài gói và chỉ thiếu file zram có thể áp dụng riêng:

```bash
sudo install -m 644 system/etc/systemd/zram-generator.conf /etc/systemd/zram-generator.conf
# Áp zswap.enabled=0 cho phiên đang chạy (nếu kernel có zswap)
if [ -e /sys/module/zswap/parameters/enabled ]; then
  printf 'N\n' | sudo tee /sys/module/zswap/parameters/enabled
fi
sudo systemctl daemon-reload
sudo systemctl start dev-zram0.swap
swapon --show
zramctl
```

Đọc/backup file đích trước khi dùng lệnh `install` nếu máy đã có cấu hình riêng.
Đây là quy trình tạo zram mới; khi zram đã hoạt động, thay size/thuật toán cần
chuyển dữ liệu ra trước hoặc reboot, không restart swap giữa lúc thiếu RAM.
Generator tự tạo unit mỗi lần boot, không cần `systemctl enable` unit zram.
Kiểm tra `zswap.enabled=0` có hiệu lực sau reboot bằng `/proc/cmdline` và
`/sys/module/zswap/parameters/enabled` (nếu tồn tại). Không tắt swap đĩa để
"chỉ dùng zram" khi còn cần hibernate. Xem [zram-generator](https://github.com/systemd/zram-generator)
và [zswap của kernel](https://www.kernel.org/doc/html/latest/admin-guide/mm/zswap.html).

## Backup/restore một lần cài file

User backup: `~/.local/state/dotfiles/backups/TIMESTAMP/`.
System/laptop backup: `/var/lib/dotfiles/backups/TIMESTAMP/` (mỗi lần cài là
transaction riêng).

```bash
./install restore "$HOME/.local/state/dotfiles/backups/TIMESTAMP" --dry-run
./install restore "$HOME/.local/state/dotfiles/backups/TIMESTAMP"
sudo ./install restore /var/lib/dotfiles/backups/TIMESTAMP
```

Chọn transaction thật được bộ cài in ra. Nếu file đích đã sửa sau khi cài,
restore dừng để bạn di chuyển/giữ bản sửa trước. Sau restore, daemon-reload và
logout/reboot nếu cần. Restore không uninstall package hoặc hoàn tác enable
service; dùng `systemctl disable` cho service muốn bỏ. Nâng cấp app có thể
đổi định dạng dữ liệu; downgrade gói không khôi phục dữ liệu cũ.

## MySQL 8.4: tùy chọn, chỉ chạy khi cần

MySQL Workbench đã có trong package list. Nếu cần server MySQL đúng dòng 8.4:

```bash
./install aur --group aur-database --prepare
# Review lại tất cả recipe/dependency trong Paru khi build.
./install aur --group aur-database --build
```

Build nguồn MySQL có thể lâu và dùng nhiều RAM/disk. Không thay bằng MariaDB
nếu project phụ thuộc hành vi MySQL. Khởi tạo **chỉ khi datadir mới chưa có dữ
liệu** theo hướng dẫn gói; thông thường:

```bash
sudo install -d -o mysql -g mysql /var/lib/mysql
sudo mysqld --initialize --user=mysql --datadir=/var/lib/mysql
```

Lưu temporary root password được mysqld ghi ra/error log. Trong `/etc/my.cnf`,
giữ các setting của gói và thêm `[mysqld] bind-address=127.0.0.1` ở dạng INI
hai dòng, để server chỉ nghe local. Kiểm tra file gói bằng `pacman -Ql mysql84`
nếu version recipe thay đổi vị trí config/unit. Với unit `mysqld.service`:

```bash
sudo systemctl start mysqld
mysql_secure_installation
mysql -u root -p < /DUONG_DAN_BACKUP/application-databases.sql
```

Tạo lại database user/grant của project từ bản backup; không dùng root trong
ứng dụng. Không `enable` service nếu muốn giữ on demand:

```bash
sudo systemctl start mysqld
sudo systemctl stop mysqld
```

## VM và container

Podman/Distrobox không cần daemon riêng để chạy container. Không enable thêm
Docker daemon trừ khi project có nhu cầu riêng. Dữ liệu container là dữ liệu
ứng dụng, không thuộc repo dotfiles.

Libvirt/virt-manager cài sẵn nhưng không enable ở boot. Chạy khi cần:

```bash
sudo systemctl start libvirtd
virt-manager
```

Nếu đã thay service mặc định hoặc dùng modular daemon, kiểm tra bằng
`systemctl list-unit-files 'virt*' 'libvirt*'`; không chạy cả hai chế độ song song.
Tắt guest trong virt-manager trước khi dừng socket/daemon:

```bash
sudo systemctl stop libvirtd.service libvirtd.socket libvirtd-ro.socket \
  libvirtd-admin.socket virtlogd.socket virtlockd.socket virtlogd.service virtlockd.service
```

Disk guest và XML phải được backup riêng. `vm-nixos [disk|iso]` chạy QEMU/KVM trực tiếp. Disk ở `~/VMs/disk/training.qcow2`,
ISO ở `~/VMs/iso/`; firmware do `edk2-ovmf` cung cấp. Tạo disk mới nếu cần:

```bash
mkdir -p ~/VMs/disk ~/VMs/iso
qemu-img create -f qcow2 ~/VMs/disk/training.qcow2 30G
```

Không chạy lệnh create đè lên disk guest đã restore.

## Chẩn đoán

Laptop dùng `./install doctor --laptop`; các lệnh pin/hibernate bên dưới dành
cho máy đã cài stage laptop. PC dùng `./install doctor` để kiểm tra phần chung.

```bash
./install doctor --laptop
systemctl --user --failed
systemctl --failed
journalctl --user -b -u swayidle -u session-lock -u swaylock -u countdown-engine
sudo journalctl -b -u greetd -u iwd -u systemd-resolved
sudo journalctl -b -u systemd-hibernate.service -u systemd-suspend-then-hibernate.service
systemctl status upower.service
upower --dump
sudo journalctl -b -u upower.service
```

Nếu screen sharing/file picker lỗi: kiểm tra `XDG_CURRENT_DESKTOP=sway` trong
`systemctl --user show-environment`, log `xdg-desktop-portal*`, và backend wlr/gtk.
Nếu dịch thuật lỗi: kiểm tra API key/network, không in key vào log/Git.
Nếu Lotus lỗi: kiểm tra user daemon, `fcitx5-lotus-server@$USER`, uinput và
profile qua `fcitx5-configtool`; đừng sửa quyền thiết bị thành 666.

Hibernate: so `resume=UUID` trong `/proc/cmdline` với `blkid` của disk swap,
`swapon --show`, dung lượng trống, hook systemd trong initramfs, log kernel.
Zram không lưu ảnh qua poweroff. Không dùng hai bản kernel/OS xen kẽ sau khi
hibernate; resume đúng bản đã hibernate trước khi chuyển boot khác.

## Dọn dẹp

Journal giới hạn 256 MiB/14 ngày. SSD TRIM weekly; trash timer xóa phần trong
thùng rác cũ hơn 30 ngày. Xem `systemctl --user list-timers` trước khi thay policy.
Không có reset-generations, nix garbage collection hoặc script tự xóa cache
package. Giữ vài gói kernel trước để có đường khôi phục; chỉ dọn khi cần dung lượng.

Chỉ dọn `src/` và `pkg/` của build đã hoàn tất; giữ recipe có sửa tay, package
archive để cài lại và transaction backup. Không xóa cả `~/.cache` hoặc tự gỡ
package theo danh sách orphan.
