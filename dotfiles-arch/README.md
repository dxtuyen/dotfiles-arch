# Arch dotfiles

[Cài Arch từ USB đến desktop Sway](docs/installation.md). Nếu đã có Arch và tài
khoản thường, bắt đầu ở [bước clone dotfiles](docs/installation.md#7-clone-dotfiles-bare).

Bare repo `~/.dotfiles.git` dùng `$HOME` làm worktree. Sửa cấu hình ngay ở
`~/.config` hoặc `~/.local`. Thư mục `~/dotfiles-arch` chứa danh sách gói,
các file hệ thống và script setup.

```bash
cd "$HOME"
dotfiles status
dotfiles diff
dotfiles add .config/sway/config
dotfiles commit -m 'Update Sway config'
dotfiles push origin main
```

Các ghi chú cho phần cứng, gói và khôi phục dữ liệu nằm trong [mục lục](docs/README.md).
