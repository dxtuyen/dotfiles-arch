# Phiên desktop

greetd gọi `/usr/local/bin/dotfiles-sway`, rồi wrapper trong `~/.local/bin/` khởi động Sway. `session-start` chuyển môi trường Wayland sang systemd user và khởi động `sway-session.target`. Trên máy mới, bật các unit phiên theo [bước áp cấu hình](installation.md#9-áp-dụng-cấu-hình-hệ-thống).

| Cần kiểm tra | Nguồn cấu hình |
| --- | --- |
| Cửa sổ và workspace | `~/.config/sway/config` |
| Thanh trạng thái | `~/.config/waybar/config` |
| Font terminal và prompt | `~/.config/foot/foot.ini`, `~/.bashrc` |
| Tắt màn hình, khóa và ngủ khi idle | `~/.config/systemd/user/swayidle.service`, `~/.local/bin/idle-suspend` |
| Nắp máy, hibernate và pin | `~/dotfiles-arch/system/etc/systemd/`, `~/dotfiles-arch/system/etc/UPower/` |

Khi đăng nhập được nhưng thiếu Waybar hoặc bộ gõ, xem `systemctl --user status sway-session.target waybar.service fcitx5.service`. Nếu không vào được Sway, kiểm tra greetd từ TTY theo [hướng dẫn cài](installation.md#11-nếu-không-vào-được-desktop).
