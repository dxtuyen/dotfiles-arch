#!/usr/bin/env bash
set -euo pipefail

if ((EUID == 0)); then
  echo 'Run as your normal login user, without sudo.' >&2
  exit 1
fi

systemctl --user daemon-reload
systemctl --user enable \
  fcitx5.service flatpak-update.timer mako.service polkit-agent.service \
  session-lock.service ssh-agent.service sway-focus-urgent.service \
  swaybg.service swayidle.service trash-clean.timer waybar.service
systemctl --user start trash-clean.timer flatpak-update.timer
