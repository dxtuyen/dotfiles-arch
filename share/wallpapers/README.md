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

Màn hình khóa giữ nền đặc cùng màu để chỉ báo/chữ rõ ràng.
