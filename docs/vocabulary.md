# GoldenDict và Anki trên máy mới

## Mặc định GoldenDict

Bộ cài tạo cấu hình **không có đường dẫn từ điển**, không bật nguồn online,
DICT server, chương trình tra cứu hoặc TTS. Các mục nguồn rỗng được ghi rõ để
GoldenDict không tự khôi phục nguồn mẫu như Wikipedia hoặc `dict.org`.
Bạn tự thêm từ điển sau ở **Edit → Dictionaries → Sources → Files**.
Cài lại cấu hình giữ nguyên đường dẫn từ điển và group đã thêm, nhưng tắt các
nguồn web/DICT/program/TTS và Forvo. Muốn dùng chúng, bật lại trong GoldenDict
sau lần chạy helper cuối cùng.

Nếu GoldenDict đang chạy lúc cài dotfiles, bộ cài hoãn cập nhật preference.
Thoát hẳn bằng **Quit/Exit trong tray**, rồi chạy:

```bash
goldendict-anki-config
```

Lệnh này không cần Anki đang mở và không tự thêm `~/Dictionary/Longman`.
Muốn thêm thư mục bằng command thay vì giao diện, dùng rõ tùy chọn:

```bash
goldendict-anki-config --dictionary "$HOME/Dictionary/Longman"
```

Đường dẫn thêm bằng helper không đệ quy: `.mdx`, `.mdd`, `.css`, `.js` và các
resource đi kèm phải nằm đúng cấu trúc của bộ từ điển. Không đổi tên riêng lẻ
file MDX/MDD/resource. Dictionary và audio là dữ liệu cá nhân, không nằm trong repo.

Giao diện dùng Modern, Dark Mode bật, **Dark Reader tắt**. Stylesheet quản lý
nền/thanh tên từ điển và các biến màu của Welcome; phần CSS Longman chỉ áp dụng
trong bài MDict chứa `.entry`. Sau khi đổi CSS, tra lại từ hoặc mở lại tab để
GoldenDict tạo trang mới. Không cần sửa CSS trong bộ dictionary cá nhân.

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

Helper áp dụng preference GoldenDict và template/CSS Longman trong repo; lần
chạy tiếp theo không ghi lại nếu đã khớp. Không tự tải từ điển, sync tài khoản,
thay field đã lưu, sửa lịch ôn hay tạo note thử. Nên hoàn tất backup/sync trước
khi áp dụng: template thay đổi sẽ ảnh hưởng cách hiển thị các note Longman cũ.
Nếu thao tác Anki API bị lỗi giữa chừng, helper cố trả template/CSS về giá trị
trước đó trong bộ nhớ; mất điện hoặc dừng process cần dùng backup Anki.

`--check` chỉ đọc cấu hình và API, dùng được khi GoldenDict đang mở; trả mã lỗi
nếu preference, deck/model/field hoặc template/CSS chưa khớp. Nó không thêm thẻ,
tạo deck/model hay áp dụng template. `--help` cũng không sửa cấu hình.

**Chỉ với collection mới hoàn toàn, không có dữ liệu cũ cần khôi phục:**

```bash
anki-longman-setup --initialize
anki-longman-setup --check
```

`--initialize` tạo deck/model còn thiếu và áp dụng template, không tạo note.
Lệnh không được dùng kèm `--check`. Khi thiếu deck/model trong chế độ thường,
helper dừng để bạn kiểm tra việc sync thay vì tự tạo dữ liệu trống.

| Preference được quản lý | Giá trị |
| --- | --- |
| AnkiConnect | Bật, `127.0.0.1:8765`, API v6 |
| Deck / model | `LongMan` / `Longman` |
| Word / Text / Sentence | `Word` / `selected_text` / `marked_sentence` |
| Add audio | Bật; lấy từ bộ dictionary nếu có |
| Nguồn web / DICT / program / TTS / Forvo | Tắt |
| Đường dẫn từ điển trên máy mới | Trống, tự thêm sau |

## Dùng hằng ngày: tra từ rồi bấm thêm

1. Mở Anki, giữ đúng profile và AnkiConnect hoạt động.
2. Tra từ trong GoldenDict, mở bài Longman rồi bấm **Send Current Article to
   Anki**; cũng có thể dùng **Ctrl+Shift+N**. Không cần bôi đen. Nếu đang có
   selection, bỏ selection trước để gửi cả bài. Với nhiều dictionary, chọn
   đúng bài Longman trước khi thêm.
3. Thẻ dùng cùng bố cục: mặt trước là từ; mặt sau rút gọn nghĩa thông thường
   đầu tiên, một ví dụ và cụm từ nếu nhận diện được, kèm IPA/loại từ khi có.
   Ưu tiên entry thông thường thay vì tên riêng/trademark đứng trước nó.
   **More details** giữ toàn bộ nội dung được gửi. Audio hiển thị một lần.
4. Sync Anki sau khi thêm từ hoặc đổi template để nhận cả nội dung và media
   trên thiết bị khác.

Phần rút gọn chạy trong template và không sửa dữ liệu gốc. Nó dùng quy tắc trên
plain text Longman, không dịch hay sinh ví dụ, và không tự biết nghĩa bạn gặp
trong bài đọc. Nếu không nhận diện được, nội dung đầy đủ vẫn hiện. Muốn học một
nghĩa khác, có thể chọn riêng nghĩa đó trước khi gửi. `marked_sentence` do
GoldenDict gửi thường chỉ là chuỗi tra cứu; ví dụ học được lấy từ nội dung
entry. Tra lại rồi thêm cùng từ có thể tạo note trùng: GoldenDict cho phép
trùng ở API, helper không tự gộp hay xóa note.

## Kiểm tra lỗi kết nối

```bash
curl --fail --silent --show-error http://127.0.0.1:8765 \
  -H 'Content-Type: application/json' \
  -d '{"action":"version","version":6}'
```

Kết quả mong đợi là `result: 6` (hoặc version mới hơn) và `error: null`.
Không kết nối được: mở Anki, kiểm tra add-on đã bật và restart sau khi cài.
`Collection lifecycle operation is active`: hoàn tất import/sync/chuyển
profile, đóng dialog import rồi thử lại. Nếu đã trở về màn hình deck nhưng
vẫn báo bận, thoát và mở lại Anki sau khi thao tác hiện tại đã kết thúc.
Không đổi port/API hay thay add-on bằng fork khác để bỏ qua lỗi này.

AnkiConnect chỉ cần bind `127.0.0.1`, port `8765`; không mở ra LAN.
GoldenDict kết nối trực tiếp nên không cần thêm wildcard CORS.
Nếu thiếu audio, kiểm tra file MDD/resource đã phục hồi và nút phát âm trong
GoldenDict trước; bật Add audio không tạo ra audio khi dictionary không có.

Thiết kế template và lệnh cập nhật Anki riêng:
[workflow notes](../lib/vocabulary/assets/anki/README.md).
Tham khảo chính thức: [Anki Sync](https://docs.ankiweb.net/manual/syncing),
[Add-ons](https://docs.ankiweb.net/manual/addons).
