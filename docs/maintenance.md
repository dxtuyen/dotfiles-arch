# Bảo trì và khôi phục

## Cập nhật

```bash
cd ~/dotfiles-arch
git status
sudo pacman -Syu
```

Đọc [Arch news](https://archlinux.org/news/) trước đợt nâng cấp lớn. Không dùng
`pacman -Sy TEN_GOI` vì tạo partial upgrade. Giữ kernel LTS. Kiểm tra ESP được
mount khi update kernel; chạy `sudo bootctl update` khi cần cập nhật bootloader.
Reboot sau update kernel/systemd rồi kiểm tra service lỗi.

AUR không tự update. Xem lại recipe khi cập nhật:

```bash
./install aur --prepare
# Xem checkout/recipe và các thay đổi từ lần trước.
./install aur --build
```

Prepare update checkout bằng fast-forward và ghi commit đã chuẩn bị. Build
không tự update source recipe. Các source `-git` bên trong PKGBUILD vẫn theo
quy tắc upstream của recipe; Arch/AUR không cung cấp khóa toàn hệ thống như Nix.
Hai gói local có commit/checksum cụ thể. Update chúng bằng cách sửa PKGBUILD,
checksum, build và kiểm tra rồi review thay đổi.

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
Các gói AUR biên dịch như Sioyek/Tofi/Lotus có thể cần rebuild sau update Qt,
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

## Đổi cấu hình

Sửa file gốc trong repo, chạy `python tools/check.py`, reload ứng dụng tương ứng.
Với symlink, không cần chạy bộ cài để thay nội dung. Thêm file/đổi manifest thì
chạy `./install user --backup --dry-run`, xem kết quả rồi `./install user --backup`.
Sửa file system thì chạy lại stage `system --backup`, reboot để áp dụng cùng lúc.
Chạy `systemctl --user daemon-reload` khi đổi unit; logout/login để test vòng đời
session, tránh restart riêng lock service khi đang thao tác.

Giữ plugin lock của Neovim trong Git sau khi review. Seed Fcitx không tự ghi đè
setting qua GUI. Muốn reset một seed, backup file đó rồi xóa riêng nó trước khi
chạy lại user stage. Không xóa cả `.config`.

## Backup/restore một lần cài file

User backup: `~/.local/state/dotfiles/backups/TIMESTAMP/`.
System backup: `/var/lib/dotfiles/backups/TIMESTAMP/`.

```bash
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
# Review ~/.cache/dotfiles/build/mysql84/
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

Disk guest và XML phải được backup riêng. `vm-nixos [disk|iso]` chạy QEMU/KVM
trực tiếp, không cần libvirt hay Nix trên host. Disk ở `~/VMs/disk/training.qcow2`,
ISO ở `~/VMs/iso/`; firmware do `edk2-ovmf` cung cấp. Tạo disk mới nếu cần:

```bash
mkdir -p ~/VMs/disk ~/VMs/iso
qemu-img create -f qcow2 ~/VMs/disk/training.qcow2 30G
```

Không chạy lệnh create đè lên disk guest đã restore.

## Chẩn đoán

```bash
./install doctor
systemctl --user --failed
systemctl --failed
journalctl --user -b -u swayidle -u session-lock -u swaylock -u countdown-engine
sudo journalctl -b -u greetd -u iwd -u systemd-resolved
sudo journalctl -b -u systemd-hibernate.service -u systemd-suspend-then-hibernate.service
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
