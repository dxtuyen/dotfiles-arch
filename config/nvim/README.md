# LazyVim

Cây cấu hình gốc link vào `~/.config/nvim`; Lua/plugin lock sửa trong checkout.
LazyVim dùng Gruvbox Material; `Ctrl+h/j/k/l` đổi cửa sổ editor, tmux dùng
`Ctrl+b` rồi `h/j/k/l`.

`packages/development.txt` cài language server, formatter, ShellCheck. Mason tắt
để tránh hai nơi quản lý cùng executable. Chạy `:LazyHealth` lần đầu,
`:Lazy restore` để dùng plugin lock, `:Lazy update` để cập nhật. Review lock sau
khi cập nhật. Thêm ngôn ngữ qua LazyVim Extras và package list tương ứng.
