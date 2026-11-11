# Cài Arch từ A đến Z

Sau khi có Arch nền và đã bootstrap Paru, có thể gom phần **gói ứng dụng** bằng
`./install apps --unattended --keep-going`; xem trước với `--dry-run` và đọc
[package workflow](packages.md). Đây là lựa chọn thay cho việc chạy từng stage
gói bên dưới, không thay các bước partition/boot/tài khoản hay áp cấu hình.

Dành cho laptop Intel: UEFI, một kernel `linux`, systemd-boot, ext4, swap riêng,
không mã hóa. USB dùng để boot bộ cài; Arch được cài vào SSD. Nếu thiết bị khác
mô tả, xác định lại tên phân vùng trước khi chạy lệnh. Không có script tự chia ổ trong repo này.

## 1. Boot USB và kết nối mạng

Boot USB Arch ở chế độ **UEFI**. Với cấu hình dưới đây, tắt Secure Boot trong
firmware; việc ký Secure Boot nằm ngoài đường cài này.

```bash
ls /sys/firmware/efi/efivars
loadkeys us
timedatectl set-ntp true
```

Nếu thư mục EFI không tồn tại, reboot chọn lại UEFI. Ethernet thường tự có
mạng. Với Wi-Fi:

```text
iwctl
device list
station wlan0 scan
station wlan0 get-networks
station wlan0 connect "TEN_WIFI"
exit
```

Thay `wlan0` bằng tên thực. Kiểm tra:

```bash
ping -c 3 archlinux.org
timedatectl status
```

## 2. Xác định SSD và chia phân vùng

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,FSTYPE,LABEL,MOUNTPOINTS
free -h
```

Phần dưới dùng **ví dụ** `/dev/nvme0n1`. Đối chiếu model, serial, dung lượng;
không chọn `/dev/sdX` chỉ vì đoán đó là SSD. Chia lại hoặc format sẽ xóa dữ liệu
trên các phân vùng được chọn.

Bố cục GPT mới:

| Phân vùng ví dụ | Dung lượng | Loại | Nơi dùng |
| --- | --- | --- | --- |
| `nvme0n1p1` | 2 GiB | EFI System | `/boot`, FAT32 |
| `nvme0n1p2` | Lớn hơn RAM | Linux swap | Swap/hibernate |
| `nvme0n1p3` | Phần còn lại | Linux filesystem | `/`, ext4; home nằm trong đó |

Ví dụ RAM 16 GiB chọn swap 24 GiB; RAM 32 GiB chọn 40 GiB. Cần còn đủ swap
trống cho ảnh hibernate; zram không thay được phân vùng này. Một kernel `linux`
dùng ESP 2 GiB. Không cần phân vùng home riêng để quản lý dotfiles.

```bash
ARCH_DISK=/dev/nvme0n1
cfdisk "$ARCH_DISK"
```

Trong cfdisk chọn GPT nếu tạo bảng mới, tạo ba phân vùng như bảng, kiểm tra
lại rồi chọn Write. Đặt đúng Type cho ESP/swap. Sau đó tự gán đúng thiết bị:

```bash
ARCH_EFI=/dev/nvme0n1p1
ARCH_SWAP=/dev/nvme0n1p2
ARCH_ROOT=/dev/nvme0n1p3
lsblk -o NAME,SIZE,MODEL,FSTYPE,LABEL,MOUNTPOINTS "$ARCH_DISK"
```

**Ba lệnh sau format các phân vùng đã chọn.** Kiểm tra biến trước khi chạy:

```bash
mkfs.fat -F 32 -n EFI "$ARCH_EFI"
mkswap -L swap "$ARCH_SWAP"
mkfs.ext4 -L arch-root "$ARCH_ROOT"
mount "$ARCH_ROOT" /mnt
mount --mkdir "$ARCH_EFI" /mnt/boot
swapon "$ARCH_SWAP"
lsblk -f "$ARCH_DISK"
findmnt /mnt/boot
```

## 3. Cài hệ thống nền

```bash
pacstrap -K /mnt base linux linux-firmware intel-ucode \
  mkinitcpio plymouth sudo iwd impala git python nano man-db man-pages
genfstab -U /mnt >> /mnt/etc/fstab
cat /mnt/etc/fstab
arch-chroot /mnt
```

Chỉ chạy `genfstab >>` một lần; nếu phải làm lại, sửa file để không trùng entry.
Trong fstab kiểm tra root ext4, ESP `/boot` và disk swap đúng UUID.
Đặt option `pri=10` cho disk swap, ví dụ:

```text
UUID=UUID_SWAP_THAT none swap defaults,pri=10 0 0
```

Zram của dotfiles dùng priority 100, kernel ưu tiên zram rồi đến disk swap.
Với ESP, thêm `umask=0077` vào options để hạn chế đọc boot files.

## 4. Locale, giờ và tài khoản trong chroot

```bash
ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime
hwclock --systohc
printf 'en_US.UTF-8 UTF-8\nvi_VN.UTF-8 UTF-8\n' >> /etc/locale.gen
locale-gen
printf 'LANG=en_US.UTF-8\n' > /etc/locale.conf
printf 'KEYMAP=us\n' > /etc/vconsole.conf
printf 'laptop\n' > /etc/hostname
cat > /etc/hosts <<'EOF'
127.0.0.1 localhost
::1 localhost
127.0.1.1 laptop.localdomain laptop
EOF
passwd
useradd -m -G wheel -s /bin/bash doxuantuyen
passwd doxuantuyen
EDITOR=nano visudo
```

Trong visudo bỏ `#` ở `%wheel ALL=(ALL:ALL) ALL`. Thay `doxuantuyen` bằng login
của bạn nếu cần. Mật khẩu root/user không lưu vào repo.

## 5. Initramfs, systemd-boot và resume

Mở `/etc/mkinitcpio.conf`, giữ các thiết lập khác cần thiết và đặt:

```bash
MODULES=(i915)
HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole plymouth block filesystems fsck)
```

Dùng hook `systemd`; nó cung cấp cơ chế resume, không thêm hook `resume` kiểu
busybox vào bộ hook trên. `i915` dành cho GPU Intel hiện tại, không phải cấu
hình dùng chung cho laptop AMD/NVIDIA.

```bash
mkinitcpio -P
ls -lh /boot/vmlinuz-* /boot/initramfs-*.img
bootctl --esp-path=/boot install
mkdir -p /boot/loader/entries
cat > /boot/loader/loader.conf <<'EOF'
default arch.conf
timeout 3
editor no
EOF
```

Lấy UUID của root và swap vừa cài:

```bash
ARCH_ROOT_UUID=$(findmnt -n -o UUID /)
ARCH_SWAP_DEVICE=$(blkid -L swap)
ARCH_SWAP_UUID=$(blkid -s UUID -o value "$ARCH_SWAP_DEVICE")
printf 'Root UUID: %s\nSwap UUID: %s\n' "$ARCH_ROOT_UUID" "$ARCH_SWAP_UUID"
test -n "$ARCH_ROOT_UUID" && test -n "$ARCH_SWAP_UUID"
cat > /boot/loader/entries/arch.conf <<EOF
title Arch Linux
linux /vmlinuz-linux
initrd /initramfs-linux.img
options root=UUID=$ARCH_ROOT_UUID rw resume=UUID=$ARCH_SWAP_UUID mem_sleep_default=deep quiet splash fbcon=nodefer
EOF
cat /boot/loader/entries/arch.conf
bootctl status
```

`microcode` hook đã ghép microcode vào initramfs. `mem_sleep_default=deep` giữ
chế độ ngủ của máy hiện tại; nếu firmware không hỗ trợ hoặc wake có lỗi, bỏ
tham số này ở entry `arch.conf` và kiểm tra lại. Máy dùng một kernel `linux`;
USB Arch và các gói kernel cũ trong cache là đường khôi phục. Không tự thêm kernel.
`fbcon=nodefer` cho console nhận framebuffer sớm để tránh đổi kích thước lúc
tuigreet bắt đầu vẽ; kiểm tra kết quả khi boot trên phần cứng thực.

## 6. Boot Arch lần đầu

Trong chroot, cấu hình Wi-Fi có DHCP và DNS ngay từ lần boot đầu:

```bash
mkdir -p /etc/iwd
cat > /etc/iwd/main.conf <<'EOF'
[General]
EnableNetworkConfiguration=true

[Network]
NameResolvingService=systemd
EOF
systemctl enable iwd.service systemd-resolved.service systemd-timesyncd.service
ln -sfn /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
exit
umount -R /mnt
reboot
```

Rút USB khi reboot. Chọn Arch, đăng nhập TTY bằng **doxuantuyen**, không phải
root. Mở Impala để chọn mạng và nhập mật khẩu; `--ascii` phù hợp console trước
khi cài Nerd Font:

```bash
impala --ascii
ping -c 3 archlinux.org
sudo -v
```

iwd lưu profile/mật khẩu trong `/var/lib/iwd`. Để tự kết nối ở các lần sau,
giữ Autoconnect bật cho mạng đã lưu; ở danh sách known networks, phím `t`
đổi trạng thái này. Impala có thể đóng sau khi kết nối.

Nếu cần CLI dự phòng, dùng `iwctl device list`, sau đó
`iwctl station wlan0 connect "TEN_WIFI"` (thay `wlan0` bằng interface thật).
Không chạy NetworkManager/wpa_supplicant để quản lý Wi-Fi này đồng thời.

## 7. Lấy repo

Chạy bằng tài khoản thường. Nếu thư mục đã tồn tại, dùng checkout đó thay vì
clone đè:

```bash
git clone https://github.com/dxtuyen/dotfiles-arch.git ~/dotfiles-arch
cd ~/dotfiles-arch
./install --help
```

## 8. Cài gói phần mềm

```bash
cd ~/dotfiles-arch
./install packages
```

Lệnh dùng `pacman -Syu --needed`, luôn full upgrade. Các nhóm là `base`,
`desktop`, `apps`, `development`, `virtualisation`; có thể chọn riêng, nhưng
đường cài đầy đủ trong hướng dẫn dùng cả năm. Danh sách nằm trong `packages/`.

AUR: đọc [quy trình package](packages.md) để bootstrap Paru sau khi review.
Không chạy makepkg/Paru bằng sudo. Sau đó:

```bash
./install aur --build --dry-run
./install aur --build --keep-going
```

Paru giải quyết cả dependency AUR-to-AUR. Review tất cả PKGBUILD, `.install`
và patch trong giao diện review trước khi chấp nhận; không dùng `--noconfirm`.
`--prepare` chỉ in PKGBUILD chính để xem trước, không ghim checkout hay thay
thế bước review lúc build. Gói đã cài được bỏ qua; cập nhật bằng Paru riêng.
Nếu recipe lỗi, các target độc lập tiếp tục với `--keep-going`, nhưng command
vẫn trả lỗi và liệt kê target thất bại. Chạy lại sau khi sửa nguyên nhân.
Ưu tiên binary có sẵn: Lotus dùng `fcitx5-lotus-bin`, overview dùng `swayview-bin`;
Sioyek giữ `sioyek-git` native để tránh hạ xuống AppImage stable 2.0.0 cũ hơn.
Tofi vẫn build vì chưa có binary tương ứng; GoldenDict-ng giữ bản nguồn mới
vì recipe AppImage trên AUR đã cũ. Các gói nguồn đã cài sẽ được bỏ qua, không
build lại mỗi lần chạy bộ cài. Xem [quyết định chọn gói](packages.md#sources).
Bibata dùng archive binary upstream qua `bibata-cursor-theme-bin` có checksum.
MySQL server tùy chọn, không phải dependency desktop.

PKGBUILD local chỉ dùng cho biến thể theme Dark Medium:

```bash
less packages/local/gruvbox-gtk-theme/PKGBUILD
./install local-packages
./install flatpak
```

Impala/iwd có binary trong kho chính thức; không có bước build ứng dụng Wi-Fi.
Sau khi vào Sway, menu mở Impala trong Foot bằng user thường, dùng màu và
phím mặc định của Impala. Việc lưu mạng và tự kết nối thuộc iwd, không phụ
thuộc cửa sổ Impala đang mở. Khi cần chia sẻ QR, tự chạy `sudo impala`.

Brave native (`brave-bin`) là trình duyệt duy nhất trong danh sách cài đặt; Brave
và VS Code bản Microsoft cài qua AUR.
TickTick cài per-user từ Flathub. Font, Qt binding cho Lotus, portal, PipeWire, các công cụ workflow
đã nằm trong danh sách chính thức.

## 9. Áp dụng cấu hình

Bước này dành cho cài mới. Trước stage `system`, đọc các file trong `system/etc/`,
đặc biệt `systemd/zram-generator.conf`, `systemd/logind.conf.d/10-laptop.conf`,
`systemd/sleep.conf.d/10-laptop.conf` và `nftables.conf`. Stage này chép cả policy
swap/ngủ/firewall; `--backup` chỉ giữ bản cũ, không bỏ qua các policy đó.
Máy đang chạy chỉ đổi giao diện thì không cần chạy lại stage `system`.

```bash
./install user --backup --dry-run
./install user --backup
sudo ./install system --user "$USER" --backup --dry-run
sudo ./install system --user "$USER" --backup
```

User stage enable các unit; chỉ timer dọn rác/update Flatpak chạy ngay. Session
lock/idle không bị gọi ở TTY. System stage chép sẵn theme Plymouth đã căn logo,
cấu hình tuigreet, tự chạy `mkinitcpio -P` rồi enable dịch vụ cho boot sau;
không restart mạng hay bật greetd giữa lúc cài. Máy mới không cần chạy script
sửa giao diện riêng. Theme có hiệu lực ở lần boot sau; boot entry và driver
được thiết lập theo phần cứng ở mục 5.

Hoàn tất DNS symlink sau khi resolved đã chạy:

```bash
sudo systemctl enable --now systemd-resolved.service
sudo cp --archive --no-clobber /etc/resolv.conf /etc/resolv.conf.before-dotfiles
sudo ln -sfn /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
resolvectl query archlinux.org
```

iwd dùng DHCP tích hợp và gửi DNS cho resolved theo `/etc/iwd/main.conf`.
Cho các user service âm thanh hoạt động theo socket/vendor preset:

```bash
systemctl --user enable --now pipewire.socket pipewire-pulse.socket wireplumber.service
./install doctor
```

Doctor kiểm tra gói, file và service; không tự sửa hay sleep máy. Nếu cố ý giữ
policy swap/ngủ khác repo, ba file tương ứng sẽ được báo khác cấu hình; không
chạy lại stage `system` chỉ để xóa cảnh báo.

Kiểm tra thêm:

```bash
cat /proc/cmdline
swapon --show
findmnt /boot
sudo bootctl status
sudo nft -c -f /etc/nftables.conf
sudo systemctl is-enabled greetd iwd systemd-resolved keyd nftables
sudo reboot
```

## 10. Đăng nhập Sway và kiểm tra thực tế

Tuigreet hiện trên VT1. Nhập user/mật khẩu; `Super+Enter` mở Foot,
`Super+D` mở Tofi. Ảnh nền Arch xanh dịu/Gruvbox đã có trong repo, không tải mạng.
Thực hiện lần lượt:

1. `systemctl --user --failed`, `systemctl --failed`: xử lý mọi service lỗi.
2. `Super+Enter`, `Super+D`, Waybar, thông báo `notify-send test` hoạt động.
3. Lotus: thử tiếng Việt trong Foot, Brave, ứng dụng GTK/Qt; `fcitx5-configtool`
   kiểm tra Lotus trong profile. Kiểm tra `sudo systemctl status fcitx5-lotus-server@$USER`.
4. `wpctl status` phải thấy loa và microphone. Máy Intel dùng SOF cần
   `sof-firmware` (đã có trong package list); nếu không có soundcard, xem
   `journalctl -k -b` để tìm lỗi firmware. Thử volume/mic/brightness và Bluetooth.
5. Network menu, Wi-Fi reconnect; thử file picker và chia sẻ màn hình qua portal.
6. `Super+O/I/G` và popup terminal; `Alt+Tab` đổi hai workspace vừa dùng.
7. `Super+C`: chạy Countdown; khóa bằng `Super+Esc`, mở khóa và xác nhận timer
   vẫn pause. Resume timer thủ công; thử screenshot/clipboard và dịch thuật.
8. `nvim`, `:Lazy restore`, `:LazyHealth`; kiểm tra language tools khi mở project.
   Xem `git diff -- config/nvim/lazy-lock.json` sau bootstrap, giữ nguyên lockfile
   nếu chỉ muốn khôi phục các phiên bản plugin đã chốt.
9. Đóng công việc đang làm, thử `systemctl suspend`, wake, nhập mật khẩu mở khóa.
10. Thử `systemctl hibernate`; bật máy, xác nhận quay lại phiên trước đó.
11. Thử `systemctl suspend-then-hibernate`; kiểm tra lid trên pin/AC và khi dock.

Khi áp dụng đầy đủ policy của repo, lid/manual sleep hoạt động trên AC; tự sleep
do idle chỉ xảy ra trên pin.
Mặc định màn hình tắt sau 5 phút, khóa sau 10 phút, ngủ sau 15 phút. Khóa thủ
công: màn hình tắt sau 10 giây. Suspend-then-hibernate dùng delay 1 giờ.
Nếu hibernate chưa hoạt động, sửa resume/swap trước khi dựa vào tự ngủ/lid.
Trong lúc sửa có thể đổi `HandleLidSwitch*` và lệnh sleep về `suspend` rồi reboot.

Kiểm tra phần cứng là bắt buộc: container không kiểm chứng được firmware,
resume, mức pin hoặc driver âm thanh thực.

## 11. Nếu không vào được desktop

`Ctrl+Alt+F2` vào TTY, đăng nhập và đọc log:

```bash
sudo systemctl status greetd
sudo journalctl -b -u greetd
journalctl --user -b -u swayidle -u session-lock -u swaylock -u countdown-engine
```

Thử `~/.local/bin/dotfiles-sway` từ TTY để thấy lỗi. Nếu đã có Sway chạy,
logout phiên đó trước. Nếu kernel mới lỗi, dùng USB Arch và hướng dẫn recovery
bên dưới; máy không có entry LTS mặc định.

Nếu không boot được: boot lại USB UEFI, kết nối mạng, mount root/ESP đúng như
mục 2, `arch-chroot /mnt`, kiểm tra fstab/entry/UUID, chạy `mkinitcpio -P` và
`bootctl --esp-path=/boot install`. Không format lại phân vùng khi đang sửa boot.
