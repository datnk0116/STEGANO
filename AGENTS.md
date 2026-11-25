# Hướng dẫn làm việc trong repo

- Đọc file này và `~/.codex/RTK.md` trước khi sửa. Mọi lệnh shell phải có tiền tố `rtk`.
- Trước khi sửa, kiểm tra `git status` và diff. Giữ nguyên mọi thay đổi, commit và file chưa theo dõi của người dùng.
- Không dùng `git checkout`, `reset`, `clean`, `restore`, `rm` hoặc thao tác ghi đè để hoàn tác nếu chưa xác định chính xác phạm vi và được người dùng yêu cầu rõ. Không revert toàn repo để sửa một file.
- Chỉ sửa đúng phần người dùng yêu cầu. Không tự thêm, xóa hoặc chép lại visualize, evidence, logbook, README hay file khác.
- Giữ nguyên Entry 06 và các evidence hiện có. Không xóa ảnh, đổi nội dung logbook, hoặc bỏ mục lịch sử nào trừ khi người dùng yêu cầu cụ thể.
- Không tự thêm vào logbook thông tin branch, commit SHA, remote, trạng thái working tree, repo audit hoặc lịch sử Git. Không thêm lời giải thích phân vai giữa STEGO và STEGANO.
- Dùng tên dự án/package `STEGANO` / `stegano` khi sửa tên được yêu cầu. Không đổi tên file hay package theo suy đoán.
- Không commit hoặc push. Nếu người dùng muốn tự commit/push, đưa lệnh chính xác sau khi hoàn tất thay đổi; không yêu cầu họ chạy lệnh có thể ghi đè phần chưa kiểm tra.
- Sau khi sửa, kiểm tra lại diff và status. Báo rõ file nào đã đổi; không nói đã chạy test nếu chưa chạy.
