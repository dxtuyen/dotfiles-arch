# Wallpaper

`desktop.svg` dùng hình dáng logo từ [Arch artwork](https://archlinux.org/art/),
đổi thành xanh dịu `#7daea3` trên nền Gruvbox `#282828` cho mục đích cá nhân.
Đây là phối màu riêng, không phải branding chính thức. Tên/logo Arch Linux
thuộc chính sách nhãn hiệu của Arch.

`desktop.png` là bản 1920×1080 có sẵn, dùng ngay sau cài. Không tải/sinh ảnh lúc
đăng nhập. Swaybg scale theo màn hình. Sau khi sửa SVG:

```bash
rsvg-convert share/wallpapers/desktop.svg -o share/wallpapers/desktop.png
systemctl --user restart swaybg.service
```

`lock.svg`/`lock.png` dùng nền tối `#1d2021`, logo Arch nhỏ phía trên và chữ
`archlinux`. Vòng khóa nhỏ nằm dưới cụm logo, ở tâm màn hình theo swaylock;
không ghim tọa độ pixel vào một độ phân giải cụ thể. Vòng không hiện thường
trực; viền sáng hơn khi nhập. Desktop giữ ảnh riêng.

```bash
rsvg-convert share/wallpapers/lock.svg -o share/wallpapers/lock.png
```
