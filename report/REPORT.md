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
- **Sleepy Alarm:** decoder căn chỉnh target và reference bằng cross-correlation, trừ hai tín hiệu trong vùng overlap rồi phân loại các mức ASK. Prefix target trước overlap được giữ nguyên để giải mã từ mẫu 0. Phép chiếu I/Q được tính riêng trên mẫu gốc của từng symbol, với pha sóng mang theo chỉ số mẫu toàn cục. Lag được đo lại khi chạy, không giả định trước một độ trễ MP3 cố định.
- **Robustness bất đối xứng:** chạy `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python scripts/run_audio_asymmetric.py`; mỗi biến thể chỉ đổi target hoặc reference, còn baseline được báo cáo riêng. Kết quả được ghi thành JSON, CSV và log.
- Chạy toàn bộ kiểm thử trong môi trường ảo đã cài dependencies: `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Mở dashboard chẩn đoán và trạng thái kiểm chứng: `streamlit run visualization/app.py`.

## 3. Phân tích kết quả

| Kiểm tra | Kết quả |
|---|---|
| Tính toàn vẹn artifact | **3/3 pass** — kích thước và SHA-256 khớp manifest |
| Blue 3 | **Exact match**, 50 ký tự: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}` |
| Sleepy Alarm, reference-assisted | **Exact match**, 39 ký tự: `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`; 350 symbol, 38 separator, `reference_assisted: true`, không lỗi byte |
| Sleepy Alarm, baseline robustness | **PASS**; baseline được tính riêng, không nằm trong mẫu số sáu biến thể |
| Sleepy Alarm, biến đổi một phía | **2/6 PASS**; cả hai phép resample round-trip PASS, bốn phép đổi gain FAIL |
| Toàn bộ unittest | **22 tests pass**, exit code 0 |

### Robustness bất đối xứng của Sleepy Alarm

Baseline reference-assisted PASS với 350 symbols, 38 separators, 39 characters và không có byte error. PASS yêu cầu `format_valid`, toàn bộ flag khớp ground truth và không có byte error. Mỗi phép biến đổi dưới đây chỉ áp dụng lên một file; file còn lại giữ nguyên.

| File được thay đổi | Gain ×0.5 | Gain ×1.5 | Resample 44.1→48→44.1 kHz |
|---|---|---|---|
| Target | **FAIL** — 28 ký tự, 14 byte errors | **FAIL** — 34 ký tự, 4 byte errors | **PASS** — 39 ký tự, 0 byte errors |
| Reference | **FAIL** — 36 ký tự, 5 byte errors | **FAIL** — 33 ký tự, 4 byte errors | **PASS** — 39 ký tự, 0 byte errors |

Hai phép resample một phía giữ được exact match; các phép đổi gain một phía không đạt tiêu chí. Đây là giới hạn quan sát được trên cặp audio Sleepy Alarm đã ghim và đúng sáu cấu hình được thử, không phải kết luận tổng quát cho audio hoặc mức gain khác. JSON, CSV và log nằm trong [results/asymmetric](../results/asymmetric/); ảnh dashboard và terminal được ghi tại [Appendix A.16](APPENDIX.md#app-a16-asymmetric-audio-robustness).

Hai test trong `tests/test_exact_match.py` dùng so sánh toàn chuỗi; flag chỉ đúng tiền tố sẽ thất bại. Regression tổng hợp mới đặt điểm overlap bên trong symbol thứ hai và xác nhận 16 nhãn đầu, mức ASK đầu tiên, cùng toàn bộ flag vẫn đúng. Lần reference-assisted ngày 19/11/2026 ghi 350 symbols, 38 separators và 39 characters; lag căn chỉnh là 1.729 mẫu, đây là độ lệch cross-correlation tìm thấy, không khẳng định toàn bộ lag chỉ do encoder MP3. Kết quả reference-free trước đó không khôi phục được flag hợp lệ và vẫn được giữ như một giới hạn của decoder.

Chi tiết các lần chạy và bằng chứng liên quan nằm trong [Logbook Entry 01](../LOGBOOK.md#entry-01), [Entry 02](../LOGBOOK.md#entry-02), [Entry 03](../LOGBOOK.md#entry-03), [Entry 04](../LOGBOOK.md#entry-04) và [Entry 05](../LOGBOOK.md#entry-05).

Đầu ra lệnh, thời gian chạy, cảnh báo và ảnh dashboard của lần kiểm chứng 3/3 artifact cùng 21 unittest được ghi tại [Appendix A.14](APPENDIX.md#app-a14-artifact-integrity-and-exact-match) và [Logbook Entry 11](../LOGBOOK.md#entry-11). Bản sửa ASK và lần chạy 22 unittest ngày 19/11, gồm JSON, log, manifest và ảnh chụp mới, nằm tại [Appendix A.15](APPENDIX.md#app-a15-ask-prefix-preservation-and-reproduction) và [Logbook Entry 12](../LOGBOOK.md#entry-12).

Phép đo robustness bất đối xứng ngày 19/11, log chạy, bảng kết quả và ảnh evidence được ghi tại [Appendix A.16](APPENDIX.md#app-a16-asymmetric-audio-robustness) và [Logbook Entry 13](../LOGBOOK.md#entry-13).

## 4. Đánh giá và phản tư

Kết quả xác nhận hai decoder trên đúng các artifact đã ghim. Blue 3 phụ thuộc bố cục vùng chéo và baseline của challenge. Sleepy Alarm cần bản reference để căn chỉnh và tách tín hiệu; kết quả này không chứng minh khả năng giải mã reference-free. Đo bất đối xứng chỉ khảo sát cặp target/reference này, hai mức gain 0.5/1.5 và resample round-trip 44.1→48→44.1 kHz; tỷ lệ 2/6 không đại diện cho độ bền trên file hoặc phép biến đổi khác. Bảo toàn artifact và so sánh nguyên chuỗi giúp phát hiện thay đổi dữ liệu hoặc sai khác dù chỉ một ký tự, nhưng các kết quả không chứng minh khả năng tổng quát hóa sang media khác.
