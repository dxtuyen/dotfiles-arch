# Khôi phục GoldenDict và Anki

## Từ điển

Khôi phục thư mục từ điển cùng file MDX, MDD và các tài nguyên đi kèm. Thoát hẳn GoldenDict, rồi áp cấu hình và thêm đúng thư mục chứa từ điển. Thay đường dẫn ví dụ bằng đường dẫn trên máy mới.

```bash
goldendict-anki-config --dictionary "$HOME/Dictionary/Longman"
goldendict-anki-config --check
```

## Khôi phục Anki trước khi áp dụng template

1. Trên máy cũ, sync collection và media. Có thể export toàn bộ collection kèm
   lịch học và media để có bản sao cục bộ trước khi chuyển máy.
2. Trên máy mới, mở Anki và đăng nhập đúng tài khoản AnkiWeb. Nếu local trống
   và AnkiWeb đã có dữ liệu, chọn **Download from AnkiWeb** khi được hỏi.
   Đợi cả collection và media sync xong. Nếu phục hồi thư mục
   `~/.local/share/Anki2` từ backup, đóng Anki trước khi chép rồi mở đúng profile.
   Không chạy hai bản Anki trên cùng collection.
3. Kiểm tra deck **`LongMan`**, note type **`Longman`** và các field
   **`Word`**, **`selected_text`**, **`marked_sentence`**, phân biệt hoa/thường.
   Template trong repo dùng một card cho mỗi note.
4. Trong **Tools → Add-ons → Get Add-ons**, cài
   [AnkiConnect, mã 2055492159](https://ankiweb.net/shared/info/2055492159), rồi
   restart Anki. Anki Sync không cài add-on cho máy mới. Nếu restore add-on từ
   backup, kiểm tra tương thích với phiên bản Anki đang dùng.
5. Giữ cửa sổ Anki chính mở, hoàn tất import/sync/chuyển profile và đóng các
   cửa sổ import/card editor. Quit GoldenDict trong tray, rồi chạy:

   ```bash
   anki-longman-setup
   anki-longman-setup --check
   ```

Lệnh setup áp template cho các note đang dùng model `Longman`. `--check` chỉ đọc và báo phần chưa khớp. Chỉ dùng `anki-longman-setup --initialize` khi chủ động tạo collection mới.

Nếu helper báo lỗi kết nối, kiểm tra AnkiConnect ở `127.0.0.1:8765` và đúng profile Anki. Nếu collection đang bận, đợi import hoặc sync xong rồi thử lại.
