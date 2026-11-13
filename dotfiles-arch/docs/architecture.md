# Tổ chức repo

Bare Git đặt worktree ở `$HOME`, metadata ở `~/.dotfiles.git`. File cấu hình
được Git theo dõi nằm ngay tại đường dẫn ứng dụng sử dụng; không có symlink farm,
manifest hay bộ cài home.

Thêm alias một lần trong `~/.bashrc`:

```bash
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME"'
```

Ẩn file home không được theo dõi:

```bash
dotfiles config --local status.showUntrackedFiles no
```

Kiểm tra trước khi thêm file mới; bare repo coi `$HOME` là worktree nhưng chỉ
theo dõi file đã `dotfiles add`.

## Đường dẫn

| Nội dung | Đường dẫn đang dùng |
| --- | --- |
| Cấu hình ứng dụng | `~/.config/APP/` |
| Lệnh người dùng | `~/.local/bin/` |
| Helper dùng chung | `~/.local/lib/dotfiles/` |
| Dữ liệu/theme | `~/.local/share/` |
| Shell | `~/.bashrc`, `~/.bash_profile`, `~/.profile` |
| User units | `~/.config/systemd/user/` |
| Cấu hình hệ thống | `~/dotfiles-arch/system/`, chép thủ công vào `/etc` |
| Package lists và hướng dẫn | `~/dotfiles-arch/` |

Sway, Waybar, Foot và popup helpers nằm ở đường dẫn chạy thật trong home. Sửa
trực tiếp rồi xem `dotfiles diff`. Seed Fcitx cũng được Git theo dõi như file
thường; nếu GUI sửa chúng, thay đổi sẽ hiện trong `dotfiles status`.

## Hệ thống và package

`pkglist.txt` liệt kê package kho chính thức. AUR, Flatpak và PKGBUILD local được
xử lý riêng bằng công cụ upstream; repo không viết package resolver.

File trong `system/` không được bare Git tự chép vào `/etc`. `setup-system.sh`
là bước root riêng, chép file và enable dịch vụ theo stage `system` hoặc
`laptop`. Đọc script và file đích trước khi chạy.

Không có `tools/`, test harness, manifest, transaction backup hay restore. Git
giữ lịch sử các file đã track; dữ liệu ứng dụng ngoài repo cần sao lưu riêng.
