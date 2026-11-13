# Cài Arch từ A đến Z

Hướng dẫn này cài Arch thủ công. Package list và cấu hình được quản lý riêng;
xem [ghi chú package](packages.md) và README sau khi hệ thống khởi động.

Dành cho laptop Intel: UEFI, một kernel `linux`, systemd-boot, ext4, swap riêng,
không mã hóa. USB dùng để boot bộ cài; Arch được cài vào SSD. Nếu thiết bị khác
mô tả, xác định lại tên phân vùng trước khi chạy lệnh. Không có script tự chia ổ trong repo này.

Phần cài dotfiles đã tách rõ: PC dùng `user` + `system`; laptop chạy thêm
`laptop`. Bạn tự chọn lệnh, không có tự nhận diện loại máy. Xem [PC/laptop](hardware.md)
cho máy khác Intel và các phần driver/mạng cần chuẩn bị riêng.

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
Dung lượng zram bằng nửa RAM, dùng zstd và chỉ chiếm RAM theo dữ liệu thực.
Khi dùng zram, tắt zswap bằng `zswap.enabled=0` trong kernel command line để
không chồng hai cơ chế nén swap. Swap đĩa vẫn giữ cho overflow và hibernate.
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
options root=UUID=$ARCH_ROOT_UUID rw resume=UUID=$ARCH_SWAP_UUID zswap.enabled=0 mem_sleep_default=deep quiet splash fbcon=nodefer
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
Không chạy NetworkManager/wpa_supplicant/dhcpcd/ConnMan để quản lý Wi-Fi này
đồng thời. iwd chỉ kết nối Wi-Fi; networkd là DHCP client duy nhất, lấy cả
gateway và DNS từ từng mạng. Match theo loại thiết bị, không phụ thuộc tên
`wlan0`, SSID hay subnet. Xem [kiểm tra địa chỉ, route và DNS](wifi.md).

## 7. Clone dotfiles bare

Sau khi migration branch được push, bare Git dùng `$HOME` làm worktree. Trên máy
mới, chạy bằng user thường:

```bash
git clone --bare git@github.com:dxtuyen/dotfiles-arch.git "$HOME/.dotfiles.git"
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME"'
dotfiles config --local status.showUntrackedFiles no
dotfiles checkout
```

Nếu checkout dừng vì file đã tồn tại, kiểm tra file đó rồi chuyển nó ra trước khi
chạy lại. Thêm alias vào `~/.bashrc` sau checkout.

## 8. Cài package

Cài gói kho chính thức và nâng cấp hệ thống cùng lúc:

```bash
sudo pacman -Syu
sudo pacman -S --needed - < "$HOME/dotfiles-arch/pkglist.txt"
```

AUR nằm trong `packages/aur.txt`. Dùng Paru bằng user thường; kiểm tra và review
PKGBUILD, dependency, `.install` và patch trước khi xác nhận. Xem
[package notes](packages.md) để bootstrap Paru. Local PKGBUILD nằm trong
`packages/local/`; build thủ công bằng `makepkg --syncdeps --install`.
Flatpak tùy chọn nằm trong `packages/flatpak.txt`.

## 9. Áp dụng cấu hình hệ thống

File cấu hình user đã ở đúng đường dẫn sau `dotfiles checkout`; không cần chạy
bộ cài. User units là tùy chọn:

```bash
cd "$HOME/dotfiles-arch"
./setup-user-services.sh
```

Trước khi áp cấu hình hệ thống, đọc các file trong `system/`. Script chép file
vào `/etc` và `/usr/local`, rồi enable service và dựng lại initramfs:

```bash
sudo ./setup-system.sh system "$USER"
```

Laptop sau khi kiểm tra swap/resume:

```bash
sudo ./setup-system.sh laptop
```

Không chạy laptop stage trên PC. Driver, boot entry, phân vùng và swap vẫn phải
chọn theo máy trong các bước cài đặt phía trên.

Impala/iwd có binary trong kho chính thức; không có bước build ứng dụng Wi-Fi.
Sau khi vào Sway, menu mở Impala trong Foot bằng user thường, dùng màu và
phím mặc định của Impala. Việc lưu mạng và tự kết nối thuộc iwd, không phụ
thuộc cửa sổ Impala đang mở. Khi cần chia sẻ QR, tự chạy `sudo impala`.

Brave native (`brave-bin`) là trình duyệt duy nhất trong danh sách cài đặt; Brave
và VS Code bản Microsoft cài qua AUR.
TickTick cài per-user từ Flathub. Font, Qt binding cho Lotus, portal, PipeWire, các công cụ workflow
đã nằm trong danh sách chính thức.

## Áp dụng cấu hình

File home đã ở đúng đường dẫn sau `dotfiles checkout`. Từ
`~/dotfiles-arch`, cài user units nếu cần và đọc script cấu hình hệ thống trước
khi chạy:

```bash
./setup-user-services.sh
sudo ./setup-system.sh system "$USER"
```

Laptop sau khi kiểm tra swap/resume:

```bash
sudo ./setup-system.sh laptop
```

System stage chép file vào `/etc`/`/usr/local`, dựng initramfs và enable dịch vụ.
Laptop stage chép policy pin/ngủ riêng. Xem [PC/laptop](hardware.md) trước khi
chọn stage. Package, user config và system config là các bước độc lập.

Hoàn tất DNS symlink sau khi resolved đã chạy:

```bash
sudo systemctl enable --now systemd-resolved.service
sudo cp --archive --no-clobber /etc/resolv.conf /etc/resolv.conf.before-dotfiles
sudo ln -sfn /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
resolvectl query archlinux.org
```

iwd tắt DHCP tích hợp theo `/etc/iwd/main.conf`; systemd-networkd dùng
`/etc/systemd/network/20-wifi.network` để nhận IP, route và DNS động. Máy đang
chạy bản cũ cần [chuyển quyền DHCP](wifi.md#áp-dụng-trên-máy-đang-dùng) từ
console tại máy hoặc reboot sau khi cài.

Cho các user service âm thanh hoạt động theo socket/vendor preset:

```bash
systemctl --user enable --now pipewire.socket pipewire-pulse.socket wireplumber.service
./check-health.sh
```

`./check-health.sh` kiểm tra các lệnh desktop cốt lõi và unit systemd lỗi.
Nó không xác minh swap/resume; hãy kiểm tra thủ công trên laptop.

Kiểm tra thêm:

```bash
cat /proc/cmdline
swapon --show
findmnt /boot
sudo bootctl status
sudo nft -c -f /etc/nftables.conf
sudo systemctl is-enabled greetd iwd systemd-networkd systemd-resolved keyd nftables
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
7. `Super+C`: nhập phút rồi xem Countdown trong popup Foot; Waybar không hiển thị timer.
   `Space` pause/resume; `Q` kết thúc timer. Icon mắt Waybar bật/tắt chống idle riêng.
   Thử screenshot/clipboard và dịch thuật.
8. `nvim`, `:Lazy restore`, `:LazyHealth`; kiểm tra language tools khi mở project.
   Xem `dotfiles diff -- .config/nvim/lazy-lock.json` sau bootstrap, giữ nguyên lockfile
   nếu chỉ muốn khôi phục các phiên bản plugin đã chốt.
9. Đóng công việc đang làm, thử `systemctl suspend`, wake, nhập mật khẩu mở khóa.
10. Laptop hoặc máy đã cấu hình hibernate: thử `systemctl hibernate`; bật máy,
    xác nhận quay lại phiên trước đó.
11. Sau stage laptop: thử `systemctl suspend-then-hibernate`; kiểm tra lid trên
    pin/AC và khi dock. PC chỉ cài phần chung không cần hai bài kiểm tra này.

Sau stage `laptop`, lid/manual sleep hoạt động trên AC; tự sleep
do idle chỉ xảy ra trên pin.
Mặc định màn hình tắt sau 5 phút, khóa sau 10 phút, ngủ sau 15 phút. Khóa thủ
công: màn hình tắt sau 10 giây. Suspend-then-hibernate không đặt delay cố định;
systemd chuyển sang hibernate khi pin yếu (dưới khoảng 5%), tùy phần cứng.
Khi máy đang thức, Waybar cảnh báo qua Mako ở 15%, UPower tự hibernate ở 10%
khi dùng pin. UPower được cài trong nhóm base và enable ở system stage;
ngưỡng hibernate 10% chỉ được áp qua stage laptop, không phụ thuộc Waybar.
Nếu hibernate chưa hoạt động, sửa resume/swap trước khi dựa vào tự ngủ/lid.
Trong lúc sửa có thể đổi `HandleLidSwitch*` và lệnh sleep về `suspend` rồi reboot.

Kiểm tra phần cứng là bắt buộc: container không kiểm chứng được firmware,
resume, mức pin hoặc driver âm thanh thực.

## 11. Nếu không vào được desktop

`Ctrl+Alt+F2` vào TTY, đăng nhập và đọc log:

```bash
sudo systemctl status greetd
sudo journalctl -b -u greetd
journalctl --user -b -u swayidle -u session-lock -u swaylock
```

Thử `~/.local/bin/dotfiles-sway` từ TTY để thấy lỗi. Nếu đã có Sway chạy,
logout phiên đó trước. Nếu kernel mới lỗi, dùng USB Arch và hướng dẫn recovery
bên dưới; máy không có entry LTS mặc định.

Nếu không boot được: boot lại USB UEFI, kết nối mạng, mount root/ESP đúng như
mục 2, `arch-chroot /mnt`, kiểm tra fstab/entry/UUID, chạy `mkinitcpio -P` và
`bootctl --esp-path=/boot install`. Không format lại phân vùng khi đang sửa boot.
