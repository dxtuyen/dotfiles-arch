# Khôi phục GoldenDict → Anki

Dictionary, Anki collection, addon và tài khoản là dữ liệu cá nhân. Bộ cài
chuẩn bị stylesheet và preference GoldenDict; không tự sync hoặc tạo collection.

1. Mở Anki, restore `~/.local/share/Anki2` hoặc sync đúng tài khoản AnkiWeb.
   Nếu collection máy mới trống và server có dữ liệu cũ, chọn Download from
   AnkiWeb khi được hỏi. Đợi media sync xong. Xác nhận deck `LongMan` và note
   type `Longman` tồn tại, phân biệt chữ hoa/thường.
2. Trong **Tools → Add-ons → Get Add-ons**, cài
   [AnkiConnect, mã 2055492159](https://ankiweb.net/shared/info/2055492159), rồi
   restart Anki. Có thể khôi phục addon đã dùng từ backup, nhưng kiểm tra nó
   tương thích phiên bản Anki mới. Upstream hiện ở
   [SourceHut](https://git.sr.ht/~foosoft/anki-connect).
3. Restore đầy đủ `.mdx`, `.mdd`, audio và resource vào `~/Dictionary/Longman`.
   Các file dictionary ở trực tiếp trong thư mục này, không thêm tầng thư mục
   vì cấu hình lookup không đệ quy.
4. Thoát hẳn GoldenDict bằng Quit/Exit trong tray; đóng card template editor của
   Anki, giữ cửa sổ Anki chính đang mở. Chạy:

   ```bash
   anki-longman-setup
   ```

   Helper cập nhật những preference được quản lý, giữ các dictionary/group
   khác; áp dụng template/CSS cho note type Longman rồi kiểm tra lại kết quả.
   Không thay field đã lưu, review history, hoặc tạo note. Nếu thiếu deck/model,
   command dừng để bạn sync dữ liệu trước.

| GoldenDict preference | Giá trị |
| --- | --- |
| AnkiConnect | Bật, `127.0.0.1:8765` |
| Deck / model | `LongMan` / `Longman` |
| Word / Text / Sentence | `Word` / `selected_text` / `marked_sentence` |
| Add audio | Bật |
| Dictionary | `~/Dictionary/Longman` |

Kiểm tra endpoint khi Anki đang mở:

```bash
curl --fail --silent --show-error http://127.0.0.1:8765 \
  -H 'Content-Type: application/json' \
  -d '{"action":"version","version":6}'
```

Kết quả có `result` dạng số và `error: null`. Không cần mở port 8765 ra LAN.
Nếu không kết nối được, kiểm tra addon đã load sau restart. Không tự thay addon
bằng một fork ngẫu nhiên hoặc đổi API version khi chưa kiểm tra khả năng tương thích.

Mở GoldenDict, rescan ở Edit → Dictionaries → Sources nếu chưa thấy Longman.
Tra một từ, chọn đúng nghĩa/example cần học rồi Send to Anki. Preview trong
Anki: nghĩa/example ngắn, audio một lần và phần Full selection mở rộng. Chọn
cả entry sẽ dùng nghĩa thông thường đầu tiên, không suy ra nghĩa bạn muốn học.
Sync lại Anki sau khi thêm từ/thay template.

Chỉ với collection mới hoàn toàn, không có dữ liệu cũ cần sync:

```bash
anki-longman-setup --initialize
```

Lệnh tạo note type/deck trống nếu thiếu, không tạo card mẫu. Thiết kế template,
Yanki CSS và lệnh áp dụng riêng ở
[workflow notes](../lib/vocabulary/assets/anki/README.md).
