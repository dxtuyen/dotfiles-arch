# Nguồn tham khảo

Đối chiếu ngày 10-11-2026. Arch/AUR có thể đổi gói/recipe; kiểm tra trên máy đích
và dùng full upgrade.

- [Arch Installation guide](https://wiki.archlinux.org/title/Installation_guide).
- [systemd-boot](https://wiki.archlinux.org/title/Systemd-boot),
  [mkinitcpio](https://wiki.archlinux.org/title/Mkinitcpio).
- [Suspend/hibernate](https://wiki.archlinux.org/title/Power_management/Suspend_and_hibernate),
  [systemd sleep](https://www.freedesktop.org/software/systemd/man/latest/systemd-sleep.conf.html).
- [Sway systemd integration](https://github.com/swaywm/sway/wiki/Systemd-integration).
- [XDG portals](https://wiki.archlinux.org/title/XDG_Desktop_Portal).
- [Fcitx5](https://wiki.archlinux.org/title/Fcitx5),
  [Lotus upstream](https://github.com/LotusInputMethod/fcitx5-lotus).
- [AUR/makepkg](https://wiki.archlinux.org/title/Arch_User_Repository).
- [GNU Stow](https://www.gnu.org/software/stow/manual/),
  [chezmoi](https://www.chezmoi.io/reference/concepts/),
  [Arch dotfiles](https://wiki.archlinux.org/title/Dotfiles).
- [Arch artwork](https://archlinux.org/art/),
  [nhãn hiệu](https://terms.archlinux.org/docs/trademark-policy/).

## Tài nguyên bên ngoài

- LazyVim starter: giữ LICENSE trong `config/nvim`.
- Flavor Gruvbox Material/plugin smart-enter của Yazi: giữ mã nguồn/license
  trong repo để không cần tải plugin lúc chạy.
- Theme GTK: Fausto-Korpsvart/Gruvbox-GTK-Theme; PKGBUILD ghim commit/checksum,
  chỉ cài biến thể Dark Medium.
- [Impala](https://github.com/pythops/impala) và
  [gói Arch chính thức](https://archlinux.org/packages/extra/x86_64/impala/).
- [Cấu hình iwd](https://man.archlinux.org/man/iwd.config.5.en) và
  [profile/Autoconnect](https://man.archlinux.org/man/iwd.network.5.en).
- [systemd.network](https://www.freedesktop.org/software/systemd/man/latest/systemd.network.html):
  match Wi-Fi station, DHCP, UseGateway/UseRoutes và DNS động.
- [ELL 0.83: DHCP lease parser](https://kernel.googlesource.com/pub/scm/libs/ell/ell/+/refs/tags/0.83/ell/dhcp-lease.c)
  và [netconfig](https://kernel.googlesource.com/pub/scm/libs/ell/ell/+/refs/tags/0.83/ell/netconfig.c):
  Router option chỉ được nhận khi dài đúng 4 byte; thiếu gateway thì không tạo default route.
  [RFC 2132 §3.5](https://www.rfc-editor.org/rfc/rfc2132.html#section-3.5)
  cho phép một danh sách router.
