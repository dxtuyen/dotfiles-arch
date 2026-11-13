#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
stage=${1:-system}
user=${2:-}

if ((EUID != 0)); then
  echo 'Run with sudo.' >&2
  exit 1
fi

copy_file() {
  local source=$1 target=$2 mode=${3:-644}
  install -D -m "$mode" "$ROOT/$source" "/$target"
}

case "$stage" in
  system)
    if [[ -z $user ]]; then
      echo "Usage: sudo $0 system USER | laptop" >&2
      exit 2
    fi
    for unit in NetworkManager.service wpa_supplicant.service dhcpcd.service connman.service; do
      if systemctl is-active --quiet "$unit" || systemctl is-enabled --quiet "$unit"; then
        echo "Disable or remove the competing network manager first: $unit" >&2
        exit 1
      fi
    done
    copy_file system/etc/bluetooth/main.conf etc/bluetooth/main.conf
    copy_file system/etc/default/earlyoom etc/default/earlyoom
    copy_file system/etc/greetd/config.toml etc/greetd/config.toml
    copy_file system/etc/greetd/vtrgb etc/greetd/vtrgb
    copy_file system/etc/iwd/main.conf etc/iwd/main.conf
    copy_file system/etc/systemd/network/20-wifi.network etc/systemd/network/20-wifi.network
    copy_file system/etc/keyd/default.conf etc/keyd/default.conf
    copy_file system/etc/modules-load.d/uinput.conf etc/modules-load.d/uinput.conf
    copy_file system/etc/nftables.conf etc/nftables.conf
    copy_file system/etc/pipewire/pipewire.conf.d/99-disable-x11-bell.conf etc/pipewire/pipewire.conf.d/99-disable-x11-bell.conf
    copy_file system/etc/systemd/journald.conf.d/10-size.conf etc/systemd/journald.conf.d/10-size.conf
    copy_file system/etc/systemd/zram-generator.conf etc/systemd/zram-generator.conf
    copy_file system/etc/wireplumber/wireplumber.conf.d/99-bluetooth-software-volume.conf etc/wireplumber/wireplumber.conf.d/99-bluetooth-software-volume.conf
    copy_file system/bin/dotfiles-sway usr/local/bin/dotfiles-sway 755
    copy_file system/etc/systemd/system/greetd.service.d/10-console.conf etc/systemd/system/greetd.service.d/10-console.conf
    copy_file system/etc/plymouth/plymouthd.conf etc/plymouth/plymouthd.conf
    copy_file share/plymouth/gruvbox-material/gruvbox-material.plymouth usr/share/plymouth/themes/gruvbox-material/gruvbox-material.plymouth
    mkinitcpio -P
    usermod -aG wheel,libvirt,kvm "$user"
    systemctl daemon-reload
    systemctl enable iwd systemd-networkd systemd-resolved systemd-timesyncd bluetooth power-profiles-daemon upower keyd earlyoom fstrim.timer nftables greetd
    systemctl enable "fcitx5-lotus-server@$user.service"
    ;;
  laptop)
    copy_file system/etc/UPower/UPower.conf.d/60-laptop.conf etc/UPower/UPower.conf.d/60-laptop.conf
    copy_file system/etc/systemd/logind.conf.d/10-laptop.conf etc/systemd/logind.conf.d/10-laptop.conf
    copy_file system/etc/systemd/sleep.conf.d/10-laptop.conf etc/systemd/sleep.conf.d/10-laptop.conf
    copy_file system/etc/systemd/system/battery-threshold.service etc/systemd/system/battery-threshold.service
    copy_file system/bin/set-battery-threshold usr/local/bin/set-battery-threshold 755
    systemctl daemon-reload
    systemctl enable battery-threshold.service
    ;;
  *)
    echo "Usage: sudo $0 system USER | laptop" >&2
    exit 2
    ;;
esac
