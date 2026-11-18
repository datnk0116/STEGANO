# STEGANO — Báo cáo đồ án thực hành CTF Jeopardy

**Học phần:** UET.CN3124 — An toàn và an ninh mạng<br>
**Chủ đề:** Steganography<br>
**Challenges:** Blue 3 (ảnh) và Sleepy Alarm (âm thanh)

## 1. Lập kế hoạch và biện minh

Đồ án khảo sát hai challenge cùng chủ đề nhưng dùng hai cách nhúng khác nhau: Blue 3 mã hóa ký tự qua sai khác RGB theo vùng chéo; Sleepy Alarm nhúng bit bằng ASK trong âm thanh. Mục tiêu là giải mã từ artifact chính thức, kiểm tra nguyên vẹn dữ liệu và xác nhận kết quả bằng toàn bộ flag.

## 2. Triển khai và tài liệu hóa

### 2.1. Artifact và nguồn

Ba artifact trong `data/` trùng các blob được thêm tại commit nguồn [`d37072a`](https://github.com/datnk0116/STEGO/commit/d37072a190b4c3fcff3e93f76c2b055b170f227f). Manifest [results/artifact_manifest.json](../results/artifact_manifest.json) ghi nguồn, kích thước và SHA-256. Lệnh `python scripts/verify_artifacts.py` kiểm tra cả kích thước lẫn checksum.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `data/blue3/blue.png` | 9,406 | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | 179,283 | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | 160,495 | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

### 2.2. Phương pháp và tái chạy

- **Blue 3:** decoder tìm baseline RGB rồi cộng sai khác theo từng vùng chéo để khôi phục ký tự.
- **Sleepy Alarm:** decoder căn chỉnh target và reference bằng cross-correlation, trừ hai tín hiệu đã căn chỉnh rồi phân loại các mức ASK. Lag được đo lại khi chạy, không giả định trước một độ trễ MP3 cố định.
- Chạy toàn bộ kiểm thử trong môi trường ảo đã cài dependencies: `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Mở dashboard chẩn đoán và trạng thái kiểm chứng: `streamlit run visualization/app.py`.

## 3. Phân tích kết quả

| Kiểm tra | Kết quả |
|---|---|
| Tính toàn vẹn artifact | **3/3 pass** — kích thước và SHA-256 khớp manifest |
| Blue 3 | **Exact match**, 50 ký tự: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}` |
| Sleepy Alarm, reference-assisted | **Exact match**, 39 ký tự: `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`; 350 symbol, 38 separator, không lỗi byte |
| Toàn bộ unittest | **21 tests pass**, exit code 0 |

Hai test trong `tests/test_exact_match.py` dùng so sánh toàn chuỗi; flag chỉ đúng tiền tố sẽ thất bại. Lần chạy được ghi nhận trước đó đo lag căn chỉnh Sleepy Alarm là 1,729 mẫu; đây là độ lệch được cross-correlation tìm thấy, không khẳng định toàn bộ lag chỉ do encoder MP3. Kết quả reference-free trước đó không khôi phục được flag hợp lệ và vẫn được giữ như một giới hạn của decoder.

Chi tiết các lần chạy và bằng chứng liên quan nằm trong [Logbook Entry 01](../LOGBOOK.md#entry-01), [Entry 02](../LOGBOOK.md#entry-02), [Entry 03](../LOGBOOK.md#entry-03), [Entry 04](../LOGBOOK.md#entry-04) và [Entry 05](../LOGBOOK.md#entry-05).

Đầu ra lệnh, thời gian chạy, cảnh báo và ảnh dashboard của lần kiểm chứng 3/3 artifact cùng 21 unittest được ghi tại [Appendix A.14](APPENDIX.md#app-a14-artifact-integrity-and-exact-match) và [Logbook Entry 11](../LOGBOOK.md#entry-11).

## 4. Đánh giá và phản tư

Kết quả xác nhận hai decoder trên đúng các artifact đã ghim. Blue 3 phụ thuộc bố cục vùng chéo và baseline của challenge. Sleepy Alarm cần bản reference để căn chỉnh và tách tín hiệu; kết quả này không chứng minh khả năng giải mã reference-free. Bảo toàn artifact và so sánh nguyên chuỗi giúp phát hiện thay đổi dữ liệu hoặc sai khác dù chỉ một ký tự, nhưng các kết quả không chứng minh khả năng tổng quát hóa sang media khác.
