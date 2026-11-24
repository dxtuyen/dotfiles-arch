# Chọn cấu hình theo máy

[Hướng dẫn cài đặt](installation.md) dùng laptop Intel với Wi-Fi và swap đĩa. Trước khi áp dụng cho máy khác, kiểm tra ba chỗ phụ thuộc phần cứng.

| Thành phần | Điều cần chọn |
| --- | --- |
| CPU và GPU | Chọn microcode theo CPU. Điều chỉnh gói video trong `pkglist.txt` và module GPU của initramfs theo card thực tế. Ví dụ `i915` dành cho laptop Intel tham chiếu. |
| Mạng | File `20-wifi.network` chỉ khớp Wi-Fi station. Với PC dùng Ethernet, tạo file `.network` khớp card có dây và bật DHCP trước lần boot đầu. |
| Ngủ và pin | PC chỉ cần stage `system`. Laptop muốn áp ngưỡng sạc, xử lý nắp và pin yếu thì thử hibernate và khôi phục phiên thành công trước khi chạy stage `laptop`. |

Stage laptop chép policy vào hệ thống và enable `battery-threshold.service` cho lần boot sau. Phân vùng swap và cấu hình resume thuộc các bước cài Arch. Cài lại stage chung trên máy có policy laptop sẽ giữ các file policy đã cài.
