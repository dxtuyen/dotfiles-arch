# Cài Arch từ A đến Z

Cài mới từ USB lên SSD cho laptop Intel dùng UEFI, systemd-boot, ext4 và
swap riêng. Quy trình đi qua môi trường USB, chroot, rồi tài khoản thường
trên máy vừa cài. Với PC hoặc GPU khác, xem [lựa chọn phần cứng](hardware.md)
trước khi chọn gói và cấu hình boot.

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

## 3. Cài hệ thống nền từ USB

```bash
pacstrap -K /mnt base linux linux-firmware intel-ucode \
  mkinitcpio plymouth sudo iwd impala git openssh python nano man-db man-pages
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

Zram dùng priority 100. Swap đĩa ở priority 10 vẫn là đích hibernate.
Với ESP, thêm `umask=0077` vào cột options của dòng `/boot`.

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

Trong chroot, xác định phân vùng swap đúng bằng `lsblk -f` rồi thay đường dẫn
ví dụ dưới đây.

```bash
lsblk -f
ARCH_ROOT_UUID=$(findmnt -n -o UUID /)
ARCH_SWAP_UUID=$(blkid -s UUID -o value /dev/nvme0n1p2)
printf 'Root UUID: %s\nSwap UUID: %s\n' "$ARCH_ROOT_UUID" "$ARCH_SWAP_UUID"
```

So hai UUID với `lsblk -f`. Khi đã xác nhận đúng root và swap đĩa, tạo boot entry.

```bash
cat > /boot/loader/entries/arch.conf <<EOF
title Arch Linux
linux /vmlinuz-linux
initrd /initramfs-linux.img
options root=UUID=$ARCH_ROOT_UUID rw resume=UUID=$ARCH_SWAP_UUID zswap.enabled=0 mem_sleep_default=deep quiet splash fbcon=nodefer
EOF
cat /boot/loader/entries/arch.conf
bootctl status
```

Hook `microcode` ghép microcode vào initramfs. Tham số `mem_sleep_default=deep`
dành cho laptop tham chiếu. Bỏ tham số này nếu firmware dùng chế độ ngủ khác.

## 6. Boot Arch lần đầu

Trong chroot, cấu hình Wi-Fi có DHCP và DNS ngay từ lần boot đầu:

```bash
mkdir -p /etc/iwd
cat > /etc/iwd/main.conf <<'EOF'
[General]
EnableNetworkConfiguration=false
EOF
mkdir -p /etc/systemd/network
cat > /etc/systemd/network/20-wifi.network <<'EOF'
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
EOF
systemctl enable iwd.service systemd-networkd.service systemd-resolved.service systemd-timesyncd.service
exit
```

Trở lại shell của USB, đặt resolver cho hệ mới rồi tháo phân vùng.

```bash
ln -sfn /run/systemd/resolve/stub-resolv.conf /mnt/etc/resolv.conf
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

iwd lưu mạng ở `/var/lib/iwd`. Nếu kết nối được Wi-Fi nhưng chưa có Internet,
kiểm tra route bằng `ip -4 route show default` và DNS bằng
`resolvectl query archlinux.org`. Xem [chẩn đoán Wi-Fi](wifi.md).

## 7. Clone dotfiles bare

Bare Git dùng `$HOME` làm worktree. Trên máy mới, dùng tài khoản thường và chuẩn
bị khóa SSH cho GitHub trước khi clone. Dùng khóa đã có quyền truy cập repo hoặc
tạo khóa bằng `ssh-keygen -t ed25519` rồi thêm khóa **công khai** vào tài khoản
GitHub có quyền truy cập. Ở lần kết nối đầu, đối chiếu fingerprint máy chủ với
danh sách chính thức của GitHub trước khi chấp nhận. Dùng `ssh -T git@github.com`
để kiểm tra GitHub nhận đúng tài khoản, rồi chạy:

```bash
git clone --bare git@github.com:dxtuyen/dotfiles-arch.git "$HOME/.dotfiles.git"
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME"'
dotfiles config --local status.showUntrackedFiles no
dotfiles checkout
```

Nếu checkout báo file trùng, kiểm tra và chuyển riêng file đó sang nơi sao lưu
rồi chạy lại. Bản `~/.bashrc` trong repo đã có alias `dotfiles`.

## 8. Cài package

Cài các gói chính thức theo danh sách của máy Intel. Nếu dùng phần cứng khác,
điều chỉnh driver trước khi cài.

```bash
sudo pacman -Syu --needed - < "$HOME/dotfiles-arch/pkglist.txt"
```

Tiếp theo, cài các gói trong `packages/aur.txt` và theme GTK local. Danh sách
Flatpak và MySQL là tùy chọn. Xem [cách cài Paru, AUR và Flatpak](packages.md).

## 9. Áp dụng cấu hình hệ thống

Từ TTY của user thường, đọc `setup-system.sh` và các file trong `system/`.
Stage `system` chép cấu hình vào hệ thống, dựng lại initramfs, thêm nhóm cho
user và enable các dịch vụ cho lần boot sau. Cài đủ các gói ở bước 8 trước,
đặc biệt là `libvirt` và `fcitx5-lotus-bin`.

```bash
cd "$HOME/dotfiles-arch"
./setup-user-services.sh
sudo ./setup-system.sh system "$USER"
systemctl --user enable --now pipewire.socket pipewire-pulse.socket wireplumber.service
```

**Laptop dùng hibernate.** Kiểm tra `swapon --show`, đối chiếu `resume=UUID=…`
trong `/proc/cmdline` với UUID swap đĩa. Lưu công việc, chạy
`systemctl hibernate`, bật máy và xác nhận quay lại đúng phiên. Sau khi thử
thành công, áp policy nắp máy, pin và sạc. PC bỏ qua lệnh này.

```bash
sudo ./setup-system.sh laptop
```

Kiểm tra `systemctl is-enabled greetd iwd systemd-networkd systemd-resolved`
rồi chạy `sudo reboot` để khởi động desktop.

## 10. Kiểm tra sau khi đăng nhập

Đăng nhập qua tuigreet, mở terminal trong Sway rồi chạy bằng user thường.

```bash
~/dotfiles-arch/check-health.sh
systemctl --user is-active sway-session.target waybar.service fcitx5.service
wpctl status
resolvectl query archlinux.org
```

Kiểm tra thấy loa và micro, gõ được tiếng Việt và kết nối lại Wi-Fi sau reboot.
Nếu đã áp policy laptop, lưu công việc rồi thử `systemctl suspend-then-hibernate`
và mở khóa sau khi đánh thức máy.

## 11. Nếu không vào được desktop

`Ctrl+Alt+F2` vào TTY, đăng nhập và đọc log:

```bash
sudo systemctl status greetd
sudo journalctl -b -u greetd
journalctl --user -b -u swayidle -u session-lock -u swaylock
```

Nếu Sway chưa chạy, thử `~/.local/bin/dotfiles-sway` từ TTY để thấy lỗi.
Nếu máy dừng trước màn hình đăng nhập, boot USB ở chế độ UEFI, mount lại root
vào `/mnt` và ESP vào `/mnt/boot` rồi vào `arch-chroot /mnt`. Kiểm tra UUID
trong fstab và boot entry. Chỉ dựng lại initramfs khi cần sửa kernel/hooks,
và chỉ cài lại systemd-boot khi file bootloader bị mất hoặc hỏng.
