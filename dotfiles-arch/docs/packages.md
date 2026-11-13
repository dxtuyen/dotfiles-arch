# Package lists

Giữ package management ở công cụ Arch và Paru. Đọc Arch news trước khi nâng cấp;
không chạy `pacman -Sy` riêng lẻ.

## Kho chính thức

Danh sách đầy đủ nằm trong `pkglist.txt`:

```bash
sudo pacman -Syu --needed
sudo pacman -S --needed - < ~/dotfiles-arch/pkglist.txt
```

Lệnh đầu full upgrade; lệnh sau cài các package trong danh sách. Chọn một trong
hai luồng phù hợp: `pacman -Syu --needed - < ...` để nâng cấp và cài cùng lúc,
hoặc hai lệnh trên để xem rõ từng bước.

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

Các package AUR đang dùng được liệt kê trong `packages/aur.txt`. Cài từng package
bằng Paru để review recipe/dependency trong lời nhắc trước khi xác nhận.
`packages/aur-database.txt` là nhóm MySQL tùy chọn. Local PKGBUILD nằm trong
`packages/local/`; đọc recipe rồi chạy `makepkg --syncdeps --install` từ thư mục
của recipe. Chạy Paru/makepkg bằng user thường, không dùng `sudo`.

Không có chế độ unattended hoặc tự động xử lý lỗi; giữ review, dependency check
và chữ ký mặc định của công cụ.

## Flatpak và inventory

`packages/flatpak.txt` ghi ứng dụng Flatpak tùy chọn. Cài thủ công với `flatpak
install --user flathub APP_ID`. Xem inventory hiện tại bằng:

```bash
pacman -Q
pacman -Qm
flatpak list --user
```

Bare Git chỉ theo dõi cấu hình; package cài đặt và trạng thái runtime vẫn do
pacman, Paru và Flatpak quản lý.
