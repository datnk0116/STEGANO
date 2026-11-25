# AGENTS.md — Hướng dẫn làm việc trong repo STEGANO

## 1. Ngữ cảnh dự án

- **Môn học:** UET.CN3124 — An toàn và an ninh mạng (ĐH Công nghệ, ĐHQGHN). Đồ án thực hành CTF Jeopardy, **bài cá nhân, 30% điểm tổng kết**, đánh giá theo CLO4 (60%) và CLO5 (40%).
- **Chủ đề duy nhất:** Steganography. Hai challenge:
  - **Blue 3** (ảnh, BYU-CSA): ký tự được mã hóa bằng tổng sai khác RGB so với màu nền trong các khối chéo của ảnh.
  - **Sleepy Alarm** (âm thanh, ImaginaryCTF 2024): dữ liệu nhúng bằng ASK (sóng mang 8 kHz, 50 baud, 3 mức biên độ: separator / bit 0 / bit 1). Giải mã cần bản gốc để căn chỉnh và trừ tín hiệu (reference-assisted). Chế độ không reference **thất bại** và phải được giữ như kết quả âm.
- **Sản phẩm nộp (theo đề):** báo cáo **PDF**, nội dung chính **≤ 15 trang** (phụ lục và tài liệu tham khảo không tính); mã nguồn/script kèm theo là khuyến khích. Tên tệp gợi ý: `MSSV_UETCN3124_CTF_Report.pdf`, `MSSV_UETCN3124_Scripts.zip`.
- **Rubric (10 điểm):** (1) Lập kế hoạch và biện minh 2.0; (2) Triển khai và tài liệu hóa 4.0; (3) Phân tích kết quả 2.0, gồm cả góc nhìn tấn công và phòng thủ; (4) Đánh giá, phản biện, tự học 2.0, gồm trích dẫn nguồn.
- **Nguyên tắc học thuật:** mọi nguồn ngoài phải trích dẫn (IEEE hoặc Vancouver, nhất quán); không sao chép writeup; chỉ thực nghiệm trên challenge được phép; giảng viên có thể vấn đáp hoặc yêu cầu chạy lại script, vì vậy mọi đoạn code phải giải thích được.

## 2. Cấu trúc thư mục và vai trò

| Đường dẫn | Vai trò | Được sửa? |
|---|---|---|
| `data/` | Artifact challenge gốc (`blue3/blue.png`, `sleepy_alarm/*.mp3`) | **Không bao giờ** |
| `src/stegano/` | Package decoder: `image.py` (Blue 3), `audio.py` (Sleepy Alarm), `cli.py`, `__main__.py` | Chỉ khi được yêu cầu; giữ API `decode_*`, `diagnose_*` |
| `src/audio_alignment.py` | Căn chỉnh audio dùng cho visualizer (module cấp cao nhất trong `src/`, không nằm trong package) | Chỉ khi được yêu cầu |
| `src/steganalysis.py` | Detector heuristic ảnh/audio, ngưỡng cố định | Chỉ khi được yêu cầu |
| `scripts/` | Chạy benchmark, robustness, verify artifact, provenance, đóng gói zip, dựng hình báo cáo | Có thể sửa; sau khi sửa phải chạy lại quality gate |
| `tests/` | `unittest`; hiện có **22 test** | Thêm được; không xóa hoặc làm yếu test |
| `visualization/` | Streamlit: `app.py` (tổng quan), `pages/1_Blue_3.py`, `pages/2_Sleepy_Alarm.py`, `plotting.py`, `utils.py` | Chỉ khi được yêu cầu |
| `results/artifact_manifest.json` | Kích thước và SHA-256 của 3 artifact, kèm URL nguồn | Chỉ đọc |
| `results/reproduction-2026-11-18/`, `reproduction-2026-11-19/`, `verification/`, `asymmetric/`, `robustness/`, `steganalysis/`, `recheck/` | Hồ sơ các lần chạy đã xảy ra (log, JSON, CSV) | **Lịch sử, không ghi đè**; lần chạy mới ghi vào thư mục mới (ví dụ `results/final/`) |
| `evidence/terminal/`, `evidence/visualization/` | Ảnh chụp màn hình gốc, không chỉnh sửa | **Không xóa, không đổi** |
| `report/REPORT.md` | Báo cáo chính (tiếng Việt), nguồn để xuất PDF | Sửa khi được yêu cầu |
| `report/APPENDIX.md` | Phụ lục A.1–A.19: hồ sơ chi tiết từng lần chạy | Giữ nguyên mục lịch sử |
| `report/figures/*.svg` | Hình sinh bởi `scripts/render_report_figures.py` | Sinh lại bằng script, không vẽ tay |
| `LOGBOOK.md` | Nhật ký Entry 00–16: lệnh, giả thuyết, lỗi, bằng chứng | Chỉ thêm entry mới ở cuối khi được yêu cầu; không sửa entry cũ |
| `README.md` | Hướng dẫn cài đặt và chạy cho người ngoài | Sửa khi được yêu cầu |
| `requirements.txt` | Dependencies (khoảng phiên bản) | Sửa khi được yêu cầu |
| `submission_package_current.zip` | Gói nộp hiện tại, sinh bởi `scripts/create_submission_zip.py` | Sinh lại bằng script, không sửa tay |

## 3. Quy tắc bất biến

1. Đọc file này trước khi sửa. Lệnh shell của agent dùng tiền tố `rtk` **chỉ khi môi trường có `rtk`**. Tiền tố này là chi tiết riêng của môi trường agent, **không được đưa vào README hoặc báo cáo mới**; ở đó chỉ ghi lệnh Python thuần.
2. Trước khi sửa, chạy `git status` và xem diff. Giữ nguyên mọi thay đổi, commit và file chưa theo dõi của người dùng.
3. Không dùng `git checkout`, `reset`, `clean`, `restore`, `rm` hoặc thao tác ghi đè để hoàn tác khi chưa xác định chính xác phạm vi và chưa được người dùng cho phép rõ ràng. Không revert toàn repo để sửa một file.
4. Chỉ sửa đúng phần được yêu cầu. Không tự thêm, xóa hoặc chép lại visualization, evidence, logbook, README hay file khác.
5. Giữ nguyên Entry 06 và mọi evidence hiện có. Không xóa ảnh, không đổi nội dung logbook, không bỏ mục lịch sử.
6. Không tự thêm vào logbook thông tin branch, commit SHA, remote, trạng thái working tree, repo audit hoặc lịch sử Git. Không thêm giải thích phân vai giữa STEGO và STEGANO.
7. Dùng tên `STEGANO` / `stegano`. Không đổi tên file hay package theo suy đoán.
8. Không commit hoặc push. Khi người dùng muốn tự commit/push, đưa lệnh chính xác sau khi hoàn tất.
9. **Trung thực kết quả:** không ghi "PASS" hoặc "đã chạy" nếu chưa chạy thành công. Không làm đẹp số liệu. Giữ các kết quả âm: reference-free thất bại, audio detector FN=5/5, robustness 1/9 và 7/23.
10. Không sao chép writeup hay code của người khác. Mọi nguồn tham khảo phải có trích dẫn và được diễn giải lại.

## 4. Vận hành

Chạy từ thư mục gốc repo (ngoài môi trường agent không cần `rtk`):

```bash
python3 -m venv .venv/repro && source .venv/repro/bin/activate
pip install -r requirements.txt

python scripts/verify_artifacts.py                          # 3/3 artifact phải PASS
PYTHONPATH=src python -m unittest discover -s tests -v      # 22 test phải đạt
PYTHONPATH=src python -m stegano blue3 data/blue3/blue.png
PYTHONPATH=src python -m stegano sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 \
    --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
python scripts/run_steganalysis_benchmark.py
python scripts/run_extended_robustness.py
python scripts/render_report_figures.py
streamlit run visualization/app.py
```

Kết quả chuẩn để đối chiếu:

- Blue 3: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}` (50 ký tự).
- Sleepy Alarm có reference: `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}` (39 ký tự, 350 symbol, 38 separator, lag 1729 mẫu).
- Sleepy Alarm không reference: thất bại (26 ký tự, 49 separator, 20 nhóm byte lỗi).

**Quality gate** (chạy sau mọi thay đổi ảnh hưởng báo cáo, script hoặc test): `scripts/create_submission_zip.py`, rồi `scripts/verify_reproducibility.py` với `--output`, `--provenance-output`, `--log-output` trỏ vào thư mục kết quả **mới**. Thay đổi `REPORT.md`, `README.md` hoặc script làm đổi hash trong provenance, nên phải chạy lại.

## 5. Quy ước viết tài liệu

- Báo cáo chính viết tiếng Việt, văn phong học thuật, bám cấu trúc đề gợi ý: Tóm tắt; Giới thiệu và mục tiêu; Bối cảnh và kiến thức nền; Môi trường và công cụ; Quy trình từng bước; Kết quả; Phân tích kỹ thuật và phòng thủ; Phần tùy biến/mở rộng; Đánh giá, hạn chế, bài học; Kết luận; Tài liệu tham khảo; Phụ lục.
- Nội dung provenance, quality gate, CRC của zip thuộc **phụ lục**, không chiếm phần thân báo cáo.
- Hình đánh số, có chú thích; trích dẫn một chuẩn thống nhất (IEEE); chỉ nêu số liệu có trong file kết quả và ghi đường dẫn nguồn.
- Bất kỳ phát biểu nào về cơ chế (vì sao decoder chạy, điều kiện thành công, giới hạn) phải kiểm chứng được bằng code hoặc log trong repo.

## 6. Định nghĩa "hoàn thành"

- Chỉ nêu file đã đổi và kết quả lệnh đã thực sự chạy (kèm exit code).
- `git status` và `git diff` được kiểm tra lại sau khi sửa; không có thay đổi ngoài phạm vi.
- 22 test vẫn đạt, 3/3 artifact vẫn PASS, hai flag vẫn khớp.