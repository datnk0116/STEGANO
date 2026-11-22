# STEGANO — Báo cáo đồ án thực hành CTF Jeopardy

**Học phần:** UET.CN3124 — An toàn và an ninh mạng<br>
**Chủ đề:** Steganography<br>
**Challenges:** Blue 3 (ảnh) và Sleepy Alarm (âm thanh)

**Sinh viên:** Nguyễn Khả Đạt<br>
**MSSV:** 24021404<br>
**Lớp:** INT3307E_3<br>
**Giảng viên:** Nguyễn Đại Thọ

## 1. Lập kế hoạch và biện minh

Đồ án khảo sát hai challenge cùng chủ đề nhưng dùng hai cách nhúng khác nhau: Blue 3 mã hóa ký tự qua sai khác RGB theo vùng chéo; Sleepy Alarm nhúng bit bằng ASK trong âm thanh. Mục tiêu là giải mã từ artifact chính thức, kiểm tra nguyên vẹn dữ liệu và xác nhận kết quả bằng toàn bộ flag.

## 2. Triển khai và tài liệu hóa

### 2.1. Artifact và nguồn

Ba artifact trong `data/` được xác định bằng kích thước và SHA-256 trong [manifest](../results/artifact_manifest.json), cùng URL nguồn challenge chính thức cho từng file. Lệnh `python scripts/verify_artifacts.py` kiểm tra kích thước và checksum.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `data/blue3/blue.png` | 9,406 | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | 179,283 | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | 160,495 | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

### 2.2. Phương pháp và kiểm thử

- **Blue 3:** decoder tìm baseline RGB rồi cộng sai khác theo từng vùng chéo để khôi phục ký tự.
- **Sleepy Alarm:** decoder căn chỉnh target và reference bằng cross-correlation, trừ hai tín hiệu trong vùng overlap rồi phân loại các mức ASK. Prefix target trước overlap được giữ nguyên để giải mã từ mẫu 0. Phép chiếu I/Q được tính riêng trên mẫu gốc của từng symbol, với pha sóng mang theo chỉ số mẫu toàn cục. Lag được đo lại khi chạy, không giả định trước một độ trễ MP3 cố định.
- **Baseline steganalysis:** detector ảnh dùng tỷ lệ màu RGB phổ biến và độ lệch chuẩn kênh; detector audio dùng năng lượng dải quanh 8 kHz và độ biến thiên RMS theo khối 50 baud. Các ngưỡng được cố định, không huấn luyện hoặc hiệu chỉnh trên tập giữ lại.
- **Benchmark:** positive samples gồm artifact chính thức và các bản biến đổi xác định; benign controls là ảnh/audio tổng hợp có seed cố định. Tập này đo baseline heuristic, không đại diện cho phân phối media thực tế.
- **Robustness bất đối xứng:** chạy `rtk proxy env PYTHONPATH=src .venv/repro314/bin/python scripts/run_audio_asymmetric.py`; mỗi biến thể chỉ đổi target hoặc reference, còn baseline được báo cáo riêng. Kết quả được ghi thành JSON, CSV và log.
- **Robustness mở rộng:** chạy `python scripts/run_extended_robustness.py`; script ghi ma trận ảnh Blue 3 và 23 lượt audio Sleepy Alarm. PASS yêu cầu format hợp lệ, exact match và không có lỗi byte.
- **Đối chiếu công cụ mã nguồn mở:** so sánh phạm vi/cách tiếp cận với Aperi'Solve, The-A-Files và WavSteg; các công cụ này không được cài hoặc chạy trong benchmark.
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
| Image baseline detector | **TP=5, TN=12, FP=0, FN=0**; precision/recall/F1 đều 1.00 trên 17 mẫu |
| Audio baseline detector | **TP=0, TN=8, FP=0, FN=5**; recall 0.00 trên 13 mẫu — baseline bỏ sót cả năm positive samples |
| Blue 3 robustness mở rộng | **1/9 PASS**; chỉ Gaussian blur radius 0.3 khôi phục exact match |
| Sleepy Alarm robustness mở rộng | **7/23 PASS**; gồm baseline và sáu phép biến đổi một phía |
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

Đầu ra lệnh, thời gian chạy, cảnh báo và ảnh dashboard của lần kiểm chứng 3/3 artifact cùng 21 unittest được ghi tại [Appendix A.14](APPENDIX.md#app-a14-artifact-integrity-and-exact-match) và [Logbook Entry 11](../LOGBOOK.md#entry-11). Bản sửa ASK và lần chạy 22 unittest ngày 19/11, gồm JSON, log, manifest và ảnh chụp mới, nằm tại [Appendix A.15](APPENDIX.md#app-a15-ask-prefix-preservation-and-output-regression) và [Logbook Entry 12](../LOGBOOK.md#entry-12).

Phép đo robustness bất đối xứng ngày 19/11, log chạy, bảng kết quả và ảnh evidence được ghi tại [Appendix A.16](APPENDIX.md#app-a16-asymmetric-audio-robustness) và [Logbook Entry 13](../LOGBOOK.md#entry-13).

### Baseline detector và benchmark

| Media | TP | TN | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ảnh | 5 | 12 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Audio | 0 | 8 | 0 | 5 | 0.00 | 0.00 | 0.00 |

Benchmark ảnh gồm 12 benign controls tổng hợp và 5 positive samples từ Blue 3 cùng các biến thể độ sáng. Benchmark audio gồm 8 benign controls tổng hợp và 5 positive samples từ Sleepy Alarm cùng các biến thể gain. Kết quả audio cho thấy baseline detector không bắt được positive sample nào trong tập này. Các mẫu tổng hợp và biến thể cùng artifact challenge không tạo thành corpus thực tế; các chỉ số chỉ mô tả bộ thử xác định này.

Reference-free Sleepy Alarm vẫn **FAIL**: 350 symbols, 49 separators, 26 ký tự giải mã được và 20 nhóm byte lỗi; `format_valid` false. Chạy với reference đạt exact match 39 ký tự, 38 separators và không có byte lỗi. Hai kết quả được ghi riêng trong [benchmark JSON](../results/steganalysis/benchmark.json).

### Ma trận robustness mở rộng

Blue 3 đạt **1/9 PASS** trên chín phép biến đổi ảnh: brightness ×0.9/×1.1, contrast ×0.9/×1.1, Gaussian blur radius 0.3, crop 16 px và Gaussian noise σ=0.5/1.0/2.0. Chỉ blur khôi phục đúng toàn bộ flag; tám biến thể còn lại thất bại.

Sleepy Alarm đạt **7/23 PASS** trong 23 lượt reference-assisted: baseline cộng 11 phép biến đổi target-only và 11 phép biến đổi reference-only. Ngoài baseline, các lượt PASS là gain ×0.75, AWGN SNR 30 dB và resample round-trip trên từng phía; các lượt còn lại giữ trạng thái FAIL. Kết quả chi tiết và các chỉ số symbol/bit/separator nằm trong [thư mục robustness](../results/robustness/).

Đối chiếu mã nguồn mở được thực hiện ở mức phạm vi: [Aperi'Solve](https://github.com/Zeecka/AperiSolve) tập trung vào phân tích ảnh và bit-plane; [The-A-Files](https://github.com/pawel-kaczmarek/The-A-Files) là framework đánh giá audio steganography/robustness; [WavSteg](https://github.com/ragibson/Steganography) xử lý LSB trong WAV. Chúng dùng phương pháp hoặc vai trò khác với RGB-delta của Blue 3 và ASK/reference differencing của Sleepy Alarm; không có kết quả chạy đối chứng được tuyên bố.

Lệnh, log và kết quả của các thí nghiệm mới nằm trong [Appendix A.17](APPENDIX.md#app-a17-steganalysis-benchmark-and-extended-robustness) và [Logbook Entry 14](../LOGBOOK.md#entry-14).

## 4. Đánh giá và phản tư

Kết quả xác nhận hai decoder trên đúng các artifact đã ghim. Blue 3 phụ thuộc bố cục vùng chéo và baseline của challenge. Sleepy Alarm cần bản reference để căn chỉnh và tách tín hiệu; kết quả reference-free không khôi phục flag hợp lệ. Baseline audio detector bỏ sót toàn bộ năm positive samples trong benchmark tổng hợp. Ma trận robustness ghi nhận 1/9 phép biến đổi ảnh và 7/23 lượt audio PASS; các tỷ lệ này mô tả đúng artifact và cấu hình đã thử, không đại diện cho độ bền trên media khác. So sánh công cụ mã nguồn mở chỉ ở mức phạm vi/phương pháp, không phải kết quả chạy đối chứng.

### 4.1. Phản biện và giới hạn suy luận

- Kiểm tra exact match chứng minh decoder khôi phục đúng chuỗi đã biết từ ba artifact cụ thể. Vì expected flags và artifact đều cố định, kết quả này chưa chứng minh khả năng phát hiện payload chưa biết hoặc tổng quát hóa sang challenge khác.
- Sleepy Alarm đạt exact match ở chế độ reference-assisted. Kết quả đó phụ thuộc bản ghi gốc; không thể diễn giải thành giải mã mù. Thử nghiệm reference-free vẫn thất bại và cần được giữ như một kết quả âm.
- Benchmark detector có 17 mẫu ảnh và 13 mẫu audio, gồm các biến thể của challenge cùng benign controls tổng hợp. Confusion matrix mô tả bộ dữ liệu nhỏ, xác định này; nó không ước lượng tỷ lệ lỗi trên ảnh/audio ngoài thực tế. Đặc biệt, audio có FN=5/5 nên heuristic hiện tại không đủ làm cổng phát hiện.
- Robustness chỉ đo các phép biến đổi và mức tham số đã nêu trên một challenge mỗi loại. Tỷ lệ PASS không đại diện cho mọi codec, thiết bị thu, nội dung hoặc cường độ biến đổi.
- SHA-256 khớp manifest xác nhận các byte hiện tại trùng giá trị đã khai báo. Nó không tự xác nhận danh tính người phát hành hay độ tin cậy của nguồn khai báo. Provenance ghi commit nguồn được khai báo trong manifest và không khẳng định đó là revision của checkout cục bộ.
- Phiên bản thư viện được ghi lúc tạo provenance, còn `requirements.txt` dùng các khoảng phiên bản thay vì lockfile. Vì vậy, provenance giúp truy vết môi trường đã chạy nhưng chưa khóa hoàn toàn môi trường cài đặt.
- Quality gate xác nhận tính toàn vẹn artifact, unittest được phát hiện trong checkout và provenance cục bộ. Không có archive hoặc manifest gói nộp để kiểm tra, nên `submission_package` phải ở trạng thái **not_verified**; quality gate cục bộ không đồng nghĩa gói nộp đã sẵn sàng.

<a id="report-quality-gate-provenance"></a>
## 5. Kiểm tra chất lượng và provenance

Chạy từ thư mục `STEGANO/` sau khi cài dependencies:

```bash
PYTHONPATH=src python scripts/verify_reproducibility.py
```

Script gọi `scripts/verify_artifacts.py`, chạy `python -m unittest discover -s tests -v`, gọi `scripts/check_provenance.py`, rồi ghi kết quả vào `results/verification/quality-gate.json` và log lệnh vào `results/verification/reproducibility.log`. Có thể tạo riêng hồ sơ nguồn bằng `python scripts/check_provenance.py`; script sinh `results/verification/provenance.json`, không cần sửa JSON bằng tay.

Quality gate ghi số test unittest phát hiện và chạy thực tế, kết quả kiểm tra ba artifact, trạng thái provenance và mã thoát từng lệnh. Trường `submission_package` được lấy trực tiếp từ kết quả `check_provenance.py`; trạng thái hiện tại là `not_verified` vì chưa có archive hoặc package manifest để kiểm tra.

Provenance ghi thời điểm tạo, các URL nguồn challenge trong manifest, phiên bản Python/thư viện, số lượng và SHA-256 của từng artifact, cùng checksum các file nguồn, script, test và cấu hình được kiểm kê. Báo cáo này nằm trong inventory; hai JSON kết quả được loại khỏi inventory để tránh vòng lặp hash.

| Quality gate | Kết quả ngày 22/11/2026 |
|---|---:|
| Unittest | **22/22** — toàn bộ test được phát hiện đều đạt |
| Artifact | **3/3** khớp kích thước và SHA-256 |
| Provenance | **verified**; 30 file nguồn được băm |
| `submission_package` | `not_verified` |

Lệnh kiểm tra hoàn tất với exit code 0. Log đầy đủ, JSON và bốn ảnh terminal được ghi trong [Appendix A.18](APPENDIX.md#app-a18-quality-gate-and-provenance). Ảnh quality gate đầu tiên giữ nguyên cả các lần thử đường dẫn thất bại trước lệnh chạy thành công; kết quả cuối cùng hiển thị rõ.

Ảnh chụp các trang dashboard hiện có, phần cần chụp lại và các hình đề xuất chưa dựng được liệt kê tại [Appendix A.19](APPENDIX.md#app-a19-visualization-evidence-review) và [Logbook Entry 16](../LOGBOOK.md#entry-16).

## 6. Đề xuất trực quan hóa

Các biểu đồ dưới đây có thể dựng trực tiếp từ dữ liệu JSON/CSV hiện có, không cần suy diễn thêm số liệu:

| Nội dung | Dạng biểu đồ và dữ liệu | Thông điệp cần làm rõ |
|---|---|---|
| Quality gate | Thẻ trạng thái cho số test thực tế, artifact, provenance và `submission_package` từ `results/verification/quality-gate.json`. | Tóm tắt lần chạy hiện tại; thể hiện rõ package chưa được xác minh. |
| Robustness | Heatmap PASS/FAIL theo phép biến đổi; Blue 3 gồm 9 trường hợp, Sleepy Alarm gồm 23 lượt và tách rõ target/reference. Nguồn: `results/robustness/*.json` và `*.csv`. | Cho thấy phép biến đổi nào làm decoder mất exact match; tách baseline khỏi biến thể. Gắn chú thích rằng đây là một artifact mỗi challenge. |
| Baseline detector | Hai confusion matrix nhỏ đặt cạnh nhau cho ảnh và audio, dùng TP/TN/FP/FN trong `results/steganalysis/benchmark.json`. | Làm rõ audio bỏ sót 5/5 positive samples; kèm cỡ mẫu để tránh hiểu nhầm là đánh giá trên corpus đại diện. |
| Provenance artifact | Sơ đồ luồng `source/manifest → artifact → SHA-256 check → kết quả quality gate`, lấy tên và trạng thái từ `results/verification/provenance.json`. | Cho người đọc lần theo nguồn đã khai báo tới byte được kiểm tra; đặt nhãn riêng cho gói nộp chưa được xác minh. |

Ưu tiên đưa thẻ quality gate và heatmap robustness lên dashboard Streamlit hiện có. Confusion matrix và sơ đồ provenance phù hợp làm hình tĩnh trong báo cáo; mỗi hình nên có số mẫu, nguồn JSON và ghi chú phạm vi ngay trong caption.

Đây là bốn đề xuất, chưa phải hình kết quả đã dựng. Ảnh dashboard trong Appendix A.19 chỉ ghi lại các trang hiện có và không thay thế các hình đề xuất này.
