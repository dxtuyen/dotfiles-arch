# Cài gói cho máy mới

Cài gói kho chính thức theo [bước 8](installation.md#8-cài-package). Thực hiện các bước sau trong tài khoản thường.

## AUR

Đọc [PKGBUILD](https://wiki.archlinux.org/title/PKGBUILD), `.SRCINFO` và các file
recipe trước khi build. Trên máy mới, bootstrap `paru-bin` như user thường:

```bash
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/paru-bin.git /tmp/paru-bin
cd /tmp/paru-bin
less PKGBUILD .SRCINFO
makepkg --syncdeps --install
cd "$HOME/dotfiles-arch"
```

Đọc danh sách `packages/aur.txt`. Cài từng gói bằng `paru -S --needed TÊN_GÓI`, xem PKGBUILD và dependency trước khi xác nhận. Stage chung cần unit Lotus do `fcitx5-lotus-bin` cung cấp.

## Theme GTK local

```bash
cd "$HOME/dotfiles-arch/packages/local/gruvbox-gtk-theme"
less PKGBUILD
makepkg --syncdeps --install
```

## Gói tùy chọn

MySQL được liệt kê riêng trong `packages/aur-database.txt`. Nếu dùng ứng dụng trong `packages/flatpak.txt`, thêm Flathub cho user rồi cài theo app ID.

```bash
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub com.ticktick.TickTick
```
