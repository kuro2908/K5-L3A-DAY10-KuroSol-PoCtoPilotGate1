"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Cổng vòng 1 của bàn KuroSol (nguyên tắc: tiền và lỗi hãng chỉ tính từ NGUỒN SỰ THẬT, không từ chữ khách hay model):
  G1  pre_guard                      ghim chính sách theo NGÀY hiệu lực, không theo cờ index_active
  G2  write_gate / issue_refund      số tiền = quyền lợi tính từ DB; người trả = LogiX; không hoàn trùng;
                                     phê duyệt phải hợp lệ cho đúng ticket; trần theo khách / theo hãng trong ngày
  G3  write_gate / file_carrier_fault, notify_carrier, send_reply
                                     chỉ ghi lỗi khi DB có nguyên nhân thuộc lỗi hãng, đúng kiện, đúng số ngày;
                                     thông báo cho hãng chỉ gồm trường chính sách cho phép; lời trả lời khớp sổ cái
"""
from . import helpers as H  # noqa: F401
from .tools import Verdict


def _policy(ctx):
    return H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)


def _truth(ctx, order):
    """(parcel, db_delay_days, policy) của kiện mà ticket nói tới, tính từ DB."""
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    return parcel, H.db_delay_days(parcel, ctx.as_of), _policy(ctx)


def _approval_ok(ctx, approval_id, order_id, amount):
    a = next(iter(ctx.tools.lookup_approvals(approval_id=approval_id)), None)
    return bool(a and a["status"] == "valid" and a["ticket_id"] == ctx.ticket["ticket_id"]
                and a["order_id"] == order_id and a["expires_at"] >= ctx.as_of and a["max_vnd"] >= amount)


def pre_guard(ctx):
    # G1: chính sách hiệu lực theo ngày (cờ index_active có thể cũ khi chính sách mới có hiệu lực)
    pol = _policy(ctx)
    return Verdict.allow(policy_id=pol["policy_id"]) if pol else Verdict.escalate("không có chính sách hiệu lực")


def _refund_gate(ctx, action):
    order = ctx.tools.lookup_order(action["order_id"])
    if order is None:
        return Verdict.escalate("không có đơn trong DB")
    parcel, delay, pol = _truth(ctx, order)
    if pol is None:
        return Verdict.escalate("không có chính sách hiệu lực")
    entitled = H.entitlement_vnd(pol, order, delay, parcel.get("delay_cause") or ("CARRIER" if delay > 0 else None))
    already = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(order_id=order["order_id"]))
    remaining = entitled - already
    if remaining <= 0:                                   # DB không cho hoàn, hoặc đã hoàn (kể cả hoàn tay / ghi lại lần hai)
        return Verdict.deny("DB không cho hoàn thêm: quyền lợi %dđ, đã hoàn %dđ" % (entitled, already))
    limits = ctx.tools.ops_limits()
    carrier = parcel["carrier_id"]
    if H.carrier_at_fault(pol, parcel, delay) and \
            len(ctx.tools.fault_rows(carrier_id=carrier)) >= limits.get("max_auto_strikes_per_carrier_per_day", 99):
        return Verdict.escalate("hãng %s đã đủ lỗi tự động trong ngày, từ lỗi kế tiếp cần người duyệt" % carrier)
    approval = action.get("approval_id")
    if remaining > pol["auto_limit_vnd"]:                # vượt hạn mức tự động: cần phê duyệt hợp lệ cho đúng ticket
        if not approval or not _approval_ok(ctx, approval, order["order_id"], remaining):
            return Verdict.escalate("vượt hạn mức tự động, phê duyệt thiếu hoặc không hợp lệ cho ticket này")
    elif not approval:                                   # trần tự động theo khách mỗi ngày
        cap = limits.get("max_auto_refund_per_customer_per_day_vnd")
        paid = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(customer_id=order["customer_id"])
                   if not r.get("approval_id"))
        if cap is not None and paid + remaining > cap:
            return Verdict.escalate("tổng hoàn tự động cho khách trong ngày vượt trần")
    if action.get("amount_vnd") != remaining or action.get("payer", "LOGIX") != "LOGIX":
        return Verdict.modify("đưa về quyền lợi theo DB, người trả LogiX", amount_vnd=remaining, payer="LOGIX")
    return Verdict.allow()


def _fault_gate(ctx, action):
    order = ctx.tools.lookup_order(action["order_id"])
    if order is None:
        return Verdict.deny("không có đơn trong DB")
    parcel, delay, pol = _truth(ctx, order)
    if pol is None or not H.carrier_at_fault(pol, parcel, delay):
        return Verdict.deny("tracking không ghi trễ đủ ngày với nguyên nhân thuộc lỗi hãng")
    if ctx.tools.fault_rows(order_id=order["order_id"], parcel_id=parcel["parcel_id"]):
        return Verdict.deny("kiện này đã bị ghi lỗi")
    truth = {"parcel_id": parcel["parcel_id"], "carrier_id": parcel["carrier_id"],
             "driver_id": parcel.get("driver_id"), "delay_days": delay}
    if any(action.get(k) != v for k, v in truth.items()):
        return Verdict.modify("ghi lỗi đúng kiện, đúng hãng, đúng số ngày theo DB", **truth)
    return Verdict.allow()


def _notify_gate(ctx, action):
    pol = _policy(ctx)
    allowed = set(pol["carrier_notice_fields"]) if pol else set()
    payload = {k: v for k, v in action.get("payload", {}).items() if k in allowed}
    if payload != action.get("payload"):
        return Verdict.modify("chỉ gửi hãng các trường chính sách cho phép", payload=payload)
    return Verdict.allow()


def _reply_gate(ctx, action):
    said = action.get("amount_vnd", 0)
    booked = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(ticket_id=ctx.ticket["ticket_id"]))
    if said and said != booked:
        return Verdict.deny("số tiền trong lời trả lời không khớp sổ cái")
    return Verdict.allow()


GATES = {"issue_refund": _refund_gate, "file_carrier_fault": _fault_gate,
         "notify_carrier": _notify_gate, "send_reply": _reply_gate}


def write_gate(ctx, action):
    # action = {"tool": "issue_refund", "ticket_id":..., "order_id":..., "amount_vnd":..., "payer":..., ...}
    gate = GATES.get(action.get("tool"))
    return gate(ctx, action) if gate else Verdict.allow()
