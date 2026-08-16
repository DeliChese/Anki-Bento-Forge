# P1-04 — AwesomeTTS tùy chọn và tạo audio theo lô an toàn

**Trạng thái:** `Đã lên kế hoạch` — chưa thay đổi mã nguồn.

**Nguồn ưu tiên:** [PERSONAL_ROADMAP.md](PERSONAL_ROADMAP.md). File này chỉ tách P1-04 thành các lát cắt có thể bàn giao độc lập.

## Quyết định sản phẩm đã chốt

- Bento Forge vẫn giữ Edge TTS hiện có; AwesomeTTS là provider **tùy chọn**, chỉ xuất hiện khi add-on đó đang được cài và bật.
- V1 tạo **audio đã lưu vào Collection Media** rồi gắn `[sound:...]`. Không dùng `{{tts}}` phát động để tránh phụ thuộc mạng khi review và để AnkiMobile đồng bộ được audio.
- Bento chỉ đọc tên preset/group công khai để người dùng chọn. Không đọc, sao chép, ghi log hay quản lý API key/cấu hình bí mật của AwesomeTTS.
- Không có fallback âm thầm từ AwesomeTTS sang Edge hay provider khác. Lỗi phải hiện rõ; fallback (nếu có) do chính preset/group của AwesomeTTS quản lý.
- Ưu tiên chất lượng hơn tốc độ: với Edge và AwesomeTTS/free endpoint, mặc định một request tại một thời điểm. Đây là chính sách bảo thủ của Bento, không phải cam kết quota từ dịch vụ bên thứ ba.

## Ranh giới không được phá vỡ

1. Không import AwesomeTTS hay `aqt` ở module domain thuần hoặc lúc import package. Adapter phải lazy-load sau khi người dùng chọn provider.
2. Callback của provider không được đụng `mw.col`, media hay UI từ worker thread. Việc đưa file vào Collection Media phải qua luồng chính/API Anki thích hợp.
3. Hủy batch chỉ hủy hàng đợi của Bento; không tuyên bố đã hủy được HTTP request mà AwesomeTTS/provider không hỗ trợ hủy.
4. Không tự đổi tốc độ giọng ở cấp provider chung: tốc độ/giọng là thuộc tính của preset AwesomeTTS. Bento chỉ điều khiển policy hàng đợi.
5. Mỗi lần chỉ làm **một** lát cắt dưới đây; không sửa đồng thời các file worker, UI và adapter.

## Lát cắt triển khai và cách giao agent

| Thứ tự | ID | Phạm vi đóng | Model / effort | Skill phải đọc khi làm | Hoàn tất khi |
| --- | --- | --- | --- | --- | --- |
| 0 | P0-04 | Sửa build artifact để đóng gói `workers/`, loại cache Python khỏi artifact và thêm test kiểm chứng nội dung gói | `gpt-5.6-terra` / `medium` | `10-testing` | Artifact mới chứa mọi module runtime cần thiết; test artifact và harness xanh |
| 1 | P1-04-A | Chuẩn hóa contract provider/audio job, policy Edge an toàn và cấu hình retry/backoff có thể test | `gpt-5.6-terra` / `high` | `04-audio-tts` | API có test unit; Edge mặc định concurrency 1; lỗi/cancel/progress có trạng thái rõ |
| 2 | P1-04-B | Adapter AwesomeTTS lazy-load: enumerate preset/group, gọi router, nhận callback, chuyển file an toàn sang media Anki | `gpt-5.6-sol` / `high` | `04-audio-tts` | Không có import bắt buộc khi AwesomeTTS thiếu; mock callback/thread/media và timeout đều có regression test |
| 3 | P1-04-C | Hàng đợi batch có checkpoint/resume, giới hạn 50 mục/lần, retry 5/15/45 giây, cooldown sau lỗi rate-limit lặp lại | `gpt-5.6-sol` / `high` | `03-batch-processing` | Dừng/tiếp tục không tạo audio trùng; 429/403/timeout không spam request; trạng thái mỗi mục truy vết được |
| 4 | P1-04-D | UI chọn provider/preset, preview một mục, cảnh báo tốc độ an toàn và i18n | `gpt-5.6-terra` / `medium` | `06-ui-layer` | UI giữ nguyên Edge khi AwesomeTTS thiếu; không freeze; mọi chuỗi mới qua `t()` |
| 5 | P1-04-E | Regression, clean-profile package check và smoke thủ công trên profile Anki đã backup | `gpt-5.6-terra` / `high` + chủ dự án thao tác | `10-testing` | Isolated suite hai vòng xanh; test provider/batch mới xanh; smoke Edge + AwesomeTTS + sync media đạt checklist |

`gpt-5.6-luna / low` chỉ phù hợp để cập nhật checklist, nhật ký và inventory sau khi các lát cắt trên đã có bằng chứng; không dùng Luna để sửa adapter/cancel/concurrency.

## Chính sách batch V1

| Tình huống | Hành vi bắt buộc |
| --- | --- |
| Edge hoặc preset AwesomeTTS/free endpoint | concurrency `1`; chờ tối thiểu 1 giây giữa các request thành công |
| Batch mới | tối đa 50 mục; hiển thị số thành công/lỗi/còn lại |
| Timeout, lỗi mạng tạm thời | retry tối đa 3 lần: 5 giây, 15 giây, 45 giây; sau đó đánh dấu lỗi, không tự chuyển provider |
| 429/403 hoặc lỗi quota lặp lại | cooldown và yêu cầu người dùng tiếp tục rõ ràng; không quay vòng request vô hạn |
| Cancel | dừng xếp request mới, lưu checkpoint; mục đang chạy có thể hoàn tất tùy provider |
| Khởi chạy lại | resume chỉ với mục chưa có audio hợp lệ; không ghi đè audio hiện có nếu người dùng không xác nhận |

Các con số trên là default V1 để giảm rủi ro bị giới hạn; chỉ nới khi đã có log test cá nhân cho provider cụ thể.

## Phụ thuộc và thứ tự chạy

```text
P0-04 artifact integrity ─┐
                          ├─> P1-04-A contract/policy ─> P1-04-B adapter
P0-02 manual backup smoke ┘                                  │
                                                              ├─> P1-04-C batch/resume ─> P1-04-D UI ─> P1-04-E verify
```

- P0-04 phải hoàn thành trước bất kỳ feature mới nào vì artifact thiếu `workers/` có thể làm add-on đóng gói hỏng ở runtime.
- P0-02 cần có checklist/profile backup trước P1-04-E; có thể chuẩn bị P1-04-A trong lúc chờ thao tác smoke, nhưng không phát hành.
- Không chạy song song P1-04-B/C/D vì cùng chạm vào giao diện audio/worker; chỉ tách test hoặc tài liệu khi không sửa file chồng lấn.

## Checklist nghiệm thu cuối

- AwesomeTTS không cài hoặc đang tắt: Bento Forge vẫn import, mở UI và dùng Edge như trước.
- Một preset/group đã cấu hình tạo được audio media local; audio phát được sau khi restart Anki và sau sync trên thiết bị thử nghiệm.
- Không có secret/preset detail nhạy cảm trong log, config Bento hoặc test fixture.
- Batch 50 mục chịu được cancel/restart/retry mà không tạo trùng hoặc khóa UI.
- Không có tuyên bố quota/SLA cho Edge hay free service; UI hiển thị đây là chế độ an toàn, chậm hơn để ổn định.

## Mẫu nhật ký khi triển khai

```md
### YYYY-MM-DD — Personal / P1-04-<lát cắt>

- Trạng thái: `Đang làm` | `Hoàn thành` | `Blocked`.
- Model / effort đã dùng: `...`.
- Phạm vi: file/module chính, không mở rộng sang lát cắt kế tiếp.
- Kiểm chứng: test cụ thể, phiên bản Anki và smoke (nếu có).
- Rủi ro còn lại / quyết định tiếp theo: ...
```
