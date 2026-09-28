# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>

> Họ và tên: Hồ Đăng Phúc  Mã học viên: 2A202602796

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Khi deploy lên Render, nếu quên set biến `AGENT_API_KEY` trong dashboard,
> `Settings()` (app/config.py) ném `ValidationError` ngay lúc container khởi
> động, container crash và platform báo "deploy failed" — tôi biết ngay để đi
> set biến.
>
> Nếu để mặc định `"changeme"`, service vẫn start bình thường, `/health` vẫn
> trả 200, mọi thứ trông "chạy được". Nhưng lúc đó ai cũng có thể gọi
> `X-API-Key: changeme` để dùng service miễn phí, tốn tiền call LLM

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> ```json
> {"event": "ask_completed", "level": "info", "timestamp": "2026-09-28T10:00:00+00:00", "user_id": "sv01", "tokens_in": 5, "tokens_out": 20, "cost_usd": 0.001}
> ```
>
> Hai việc làm được nhờ log dạng JSON mà `print` không làm được:
>
> 1. **Lọc/truy vấn theo trường**: có thể `jq 'select(.user_id=="sv01")'`
>    hoặc query trên dashboard log của Render để lấy đúng log của một user,
>    hoặc tính tổng `cost_usd` theo ngày — với `print` chỉ có chuỗi text, phải
>    tự viết regex để parse, dễ vỡ khi nội dung câu trả lời chứa dấu phẩy hay
>    xuống dòng.
> 2. **Dựng cảnh báo/biểu đồ tự động**: một hệ thống giám sát (Grafana,
>    CloudWatch...) có thể đọc trực tiếp field `cost_usd` hoặc `tokens_out`
>    để vẽ biểu đồ chi phí theo giờ, hoặc bắn cảnh báo khi `level: "error"` —
>    `print("đã trả lời xong")` không mang thông tin nào để máy xử lý, chỉ
>    con người đọc được.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ... MB |
| Multi-stage | ... MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Repo hiện chỉ còn một Dockerfile (bản multi-stage đã sửa); bản 1-stage gốc
> chỉ còn tồn tại dưới dạng mô tả trong comment đầu file, không có file riêng
> để build so sánh trực tiếp. Về lý thuyết/kinh nghiệm chung với `python:3.11`:
>
> | Bản | Dung lượng |
> |-----|-----------|
> | 1 stage (bản đầu) | ~950 MB |
> | Multi-stage | ~180 MB |
>
> Phần chênh lệch chủ yếu là: build tool-chain (gcc, các gói `-dev` mà pip cần
> lúc compile), cache của `pip` (`~/.cache/pip`), và toàn bộ `requirements.txt`
> nằm lẫn trong layer chứa cả source code. Ở bản multi-stage, stage `builder`
> cài đặt xong rồi chỉ copy đúng thư mục `/install` (site-packages đã build
> sẵn) sang stage `runtime` sạch, không mang theo compiler hay cache pip —
> image cuối chỉ có Python runtime + thư viện đã cài + code, không có công cụ
> build.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Dockerfile hiện tại copy theo thứ tự: `COPY requirements.txt .` → `RUN pip
> install ...` → (sau khi sang stage runtime) `COPY app ./app`, `COPY utils
> ./utils`. Khi chỉ sửa một ký tự trong `app/main.py` rồi build lại:
> - Layer `COPY requirements.txt .` và `RUN pip install` **dùng lại cache**
>   (hash của `requirements.txt` không đổi).
> - Layer `COPY app ./app` trở đi **phải chạy lại** vì nội dung thư mục `app`
>   đã đổi, mọi layer sau nó trong stage runtime cũng invalidate theo.
>
> Nếu đặt `COPY . .` lên trước `RUN pip install`: chỉ cần sửa bất kỳ file nào
> trong repo (kể cả file không liên quan tới dependency như `app/main.py`)
> cũng làm layer `COPY . .` đổi hash, khiến `RUN pip install` — bước tốn thời
> gian nhất (tải và compile hàng chục package) — bị chạy lại từ đầu mỗi lần,
> dù `requirements.txt` không hề thay đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện nếu chạy root: (1) code Python có lỗ hổng (ví dụ một
> dependency dính RCE, hoặc endpoint bị inject để ghi/đọc file tuỳ ý) → (2)
> kẻ tấn công thực thi lệnh với quyền của process, tức root bên trong
> container → (3) root trong container có UID 0, trùng UID 0 của host → (4)
> nếu container có mount volume từ host, hoặc thoát được container qua lỗ
> hổng kernel/runtime (container escape), kẻ tấn công với UID 0 sẽ có toàn
> quyền trên các file/tài nguyên đó ở host, biến một lỗi ứng dụng thành chiếm
> quyền hệ thống.
>
> Dockerfile của tôi có `RUN useradd --create-home --uid 10001 appuser` rồi
> `USER appuser` trước `CMD`. Việc này cắt chuỗi ở bước (2)–(3): dù code bị
> khai thác, process chỉ chạy với UID 10001 không có quyền ghi ngoài thư mục
> của nó, không trùng UID root của host — kẻ tấn công chiếm được shell trong
> container cũng chỉ có quyền một user thường, giới hạn thiệt hại trong phạm
> vi container.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa **20 request** trong 2 giây liên tiếp.
>
> Cách đạt được: gửi 10 request vào giây 59 của phút hiện tại (đúng hạn mức
> 10/phút, không bị chặn vì bộ đếm của phút này vẫn dưới 10) rồi ngay giây 00
> của phút kế tiếp, bộ đếm reset về 0 — gửi tiếp 10 request nữa, đầy đủ hạn
> mức 10/phút mới. Tổng cộng 20 request lọt qua chỉ trong khoảng 1–2 giây
> quanh ranh giới phút, vì hệ thống chỉ nhìn "phút đồng hồ hiện tại" mà không
> quan tâm 60 giây gần nhất thực sự có bao nhiêu request.
>
> Với sliding window 60 giây thực sự (như `app/rate_limiter.py` dùng Redis
> ZSET, xóa các entry cũ hơn `now - 60`), việc này không xảy ra được vì bất kỳ
> thời điểm nào, số request trong 60 giây gần nhất cũng bị giới hạn đúng 10,
> không có "ranh giới" để lách.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limiter (`app/rate_limiter.py`) giới hạn **số lượng request** trong
> cửa sổ 60 giây (Redis ZSET, key `ratelimit:{user_id}`), không quan tâm mỗi
> request tốn bao nhiêu tiền. Cost guard (`app/cost_guard.py`) giới hạn
> **tổng chi phí (USD) trong tháng** (Redis string `cost:{user_id}:{YYYY-MM}`
> cộng dồn bằng `INCRBYFLOAT`), không quan tâm request đến nhanh hay chậm.
>
> - Rate limit cho qua nhưng cost guard phải chặn: user gửi chỉ 3 request/phút
>   (dưới hạn mức 10/phút) nhưng mỗi request là một câu hỏi rất dài, tốn
>   nhiều token, khiến tổng chi phí trong tháng vượt `monthly_budget_usd`
>   (mặc định 10.0) — rate limiter không phát hiện được vì tần suất thấp,
>   cost guard phải chặn ở bước `guard.check()`.
> - Ngược lại, rate limit chặn nhưng cost guard cho qua: user spam 15 request
>   rất ngắn ("hi") trong 1 phút — mỗi request rẻ, tổng chi phí còn xa ngưỡng
>   budget, nhưng vượt hạn mức 10 request/phút nên bị `limiter.check()` trả
>   429 trước khi cost guard kịp xem xét.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Hiện tại `/health` (main.py:76-92) chỉ kiểm tra `lifecycle.shutting_down`,
> **không** đụng tới Redis — trả 200 miễn container còn sống. `/ready`
> (main.py:95-111) mới gọi `store.ping()` để kiểm tra Redis, trả 503 nếu mất
> kết nối. Load balancer/orchestrator dùng `/ready` để quyết định có route
> traffic vào container hay không, và dùng health/liveness riêng để quyết
> định có restart container hay không.
>
> Nếu gộp làm một endpoint vừa đóng vai liveness vừa kiểm tra Redis, khi Redis
> rớt 30 giây, thứ tự sự kiện trên cụm 3 container:
> 1. Redis mất kết nối → cả 3 container cùng lúc gọi endpoint gộp đều nhận
>    `store.ping()` thất bại → trả về 503.
> 2. Orchestrator coi 503 là "liveness fail" (vì đây cũng là endpoint
>    liveness) chứ không chỉ là "chưa sẵn sàng" → sau vài lần probe thất bại
>    liên tiếp, nó **restart cả 3 container cùng lúc**.
> 3. Trong lúc cả 3 container đang restart, không còn container nào chạy để
>    nhận request → toàn bộ service downtime, dù nguyên nhân gốc chỉ là Redis
>    chập chờn 30 giây và sẽ tự hồi phục.
> 4. Container mới khởi động lại, gọi Redis lần nữa — nếu Redis đã kết nối
>    lại thì health check pass, nhưng service đã trải qua một khoảng downtime
>    hoàn toàn không cần thiết, thay vì chỉ tạm thời bị loại khỏi load
>    balancer (điều mà tách riêng `/ready` sẽ làm, không cần restart).

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Với lịch sử lưu trong Redis (`app/store.py`, key `history:{user_id}` dùng
> Redis List, `RPUSH`/`LTRIM`/`EXPIRE`), khi scale 3 container và gọi `/ask`
> nhiều lần với cùng `X-User-Id`, mỗi request có thể rơi vào container khác
> nhau (round-robin của `docker compose`/nginx) nhưng `history_length` vẫn
> **tăng dần đều và nhất quán** (0, 1, 2, 3, ...) vì cả 3 container đọc/ghi
> chung một Redis — trạng thái nằm ngoài process.
>
> Nếu lịch sử lưu trong một dict Python trong bộ nhớ process, mỗi container
> sẽ có dict riêng, không chia sẻ nhau. `history_length` sẽ **không tăng đều**
> mà nhảy lộn xộn tuỳ request rơi vào container nào: ví dụ container A đã
> thấy 3 request trước đó nên trả `history_length=3`, nhưng request kế tiếp
> rơi vào container B (chưa từng thấy user này) sẽ trả `history_length=0`.
> Ngoài ra nếu một container restart, dict của riêng nó mất sạch lịch sử dù
> hai container kia vẫn còn — đúng là vấn đề mà việc dùng Redis (state ngoài
> process) giải quyết để service thật sự stateless và scale ngang được.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Lỗi gặp phải: gọi `<URL>/ready` sau lần deploy đầu tiên trên Render trả về
> `503 {"status":"not ready","redis":false}` dù `/health` vẫn 200 bình
> thường.
>
> Cách tìm nguyên nhân: vì `/health` không đụng Redis còn `/ready` có gọi
> `store.ping()`, 503 riêng ở `/ready` cho biết ngay vấn đề nằm ở kết nối
> Redis chứ không phải app crash. Xem log container trên Render thấy lỗi kết
> nối tới Redis, kiểm tra lại biến `REDIS_URL` thì phát hiện tôi đã dán nhầm
> **external URL** của Render Key Value add-on (dùng để nối từ máy local) vào
> thay vì **internal URL** — external URL không mở kết nối được từ bên trong
> mạng nội bộ của Render hoặc bị giới hạn khác về network.
>
> Cách sửa: vào dashboard của Redis add-on, copy đúng "Internal Redis URL",
> cập nhật lại biến môi trường `REDIS_URL` của service, service tự redeploy,
> gọi lại `/ready` thấy `{"status":"ready","redis":true}` — xác nhận đã hết
> lỗi.
