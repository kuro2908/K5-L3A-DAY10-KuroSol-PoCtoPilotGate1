# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): KuroSol
- Lớp: `L3A`
- Repo của bàn: `K5-L3A-DAY10-KuroSol-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): (chưa bốc; điền sau khi nhận thẻ ở vòng 2)

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Vũ Nhật Minh | 2A202603711 | Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (đảm nhiệm cả ba vai) | ✓ |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## VuNhatMinh-2A202603711

### Phần việc phụ trách

Trưởng nhóm, đảm nhiệm cả ba vai. Phiếu A (A1–A5), Phiếu B (B0–B8), `config/acceptance_criteria.json`, `lab10/guards.py` (cổng G1–G3), `config/operating_gates.json`, TEAM.md.

### Đóng góp cụ thể

Viết Bản tiêu chí và ký trước lần đo đầu tiên; chạy mốc base, after, prepared; viết ba cổng vòng 1 (ghim chính sách theo ngày; số tiền, người trả và approval theo DB; lỗi hãng và thông báo gửi hãng theo DB); đặt con số kinh doanh, vận hành, pháp lý; viết runbook 1–3 và giờ cao điểm; chốt vòng 1 và quyết định v1.

**Dùng AI:** Claude Code (Claude Sonnet 5.5) hỗ trợ đọc code, viết và chạy `guards.py`, soạn Phiếu A và B và chạy các lệnh trong container Docker (máy chưa cài Python). Các ngưỡng, con số và quyết định phải được Minh đọc lại và giải thích được khi demo.

### Bằng chứng

Commit ký tiêu chí `87cdb9f` (hash tiêu chí `4d239e27`); hash chốt vòng 1 `19b46eba`; lần chạy `R-base-before-20261118-112904-bde05c`, `R-base-after-20261118-113044-e87e3f`, `R-base-prepared-20261118-113122-e87e3f`; Phiếu A mục A1–A5, Phiếu B mục B0–B8.

### Exit ticket

(Bản nháp, Minh sửa lại bằng lời của mình.) Học được: cổng tốt nhất là cổng tính từ nguồn sự thật chứ không tin chữ khách hay model, và chỉ một chỉ số "pass_rate cao" vẫn che được thiệt hại lên bên thứ ba. Còn chưa chắc: cổng có chịu được bộ test ẩn và giờ cao điểm gấp ba với chỉ một người duyệt không.
