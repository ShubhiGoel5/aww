# Legal AI Platform v2 — Full Legal Department Replacement

> **Tm nhn:** Thay th hon ton b phn php l truyn thng trong doanh nghip.
> Khng ch chatbot — m l mt **Legal Operating System**.

---

## 1. Product Vision

```
TRC (Truyn thng):                    SAU (Legal AI Platform):
                                         
Thu lut s ─── 15-50tr/thng          ┌─────────────────────────┐
Hire Legal Staff ── 10-20tr/thng        │   LEGAL AI PLATFORM     │
                                         │                         │
Son H ──── 2-3 day                   │   Son H ── 5 pht    │
Review H ── 1-2 day                   │   Review ─── 30 giy    │
Tra cu lut ── vi gi                 │   Tra cu ── tc th    │
Son ni rule ── 1 tun                  │   Ni rule ── 10 pht    │
T vn ───── t lch, ch             │   T vn ─── 24/7       │
                                         │                         │
Chi ph: 30-70tr/thng                   │   Chi ph: 3-8tr/thng  │
                                         └─────────────────────────┘
```

---

## 2. Platform Modules

```
┌─────────────────────────────────────────────────────────────┐
│                    LEGAL AI PLATFORM                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  📄 DRAFT    │  │  🔍 REVIEW   │  │  💬 CONSULT      │   │
│  │  Son tho   │  │  R sot     │  │  T vn          │   │
│  │  vn bn     │  │  hp ng    │  │  php l         │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  📚 LIBRARY  │  │  ✅ COMPLY   │  │  📊 MANAGE       │   │
│  │  Th vin    │  │  Tun th    │  │  Qun l         │   │
│  │  mu & lut  │  │  php lut   │  │  vn bn DN      │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  🔄 BATCH    │  │  🔌 API      │                         │
│  │  X l      │  │  Tch hp    │                         │
│  │  hng lot   │  │  h thng    │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Module 1: DRAFT (Son tho)
**Thay th:** Lut s son hp ng, admin son vn bn
```
Input:  Loi vn bn + thng tin cn thit
Output: Vn bn hon chnh (Word/PDF), ng php lut

H tr:
├── Hp ng (lao ng, dch v, mua bn, thu, hp tc, i l)
├── Ph lc (gia hn, sa i, b sung, thanh l)
├── Vn bn ni b (ni rule, rule ch, rulet regulation, thng bo, bin bn)
├── Vn bn i ngoi (cng vn, giy y rulen, n khiu ni)
├── HR documents (HL, rulet regulation lng, k lut, sa thi, BHXH)
└── Bo co php l (tun th, r sot, nh gi ri ro)
```

### Module 2: REVIEW (R sot)
**Thay th:** Lut s review hp ng
```
Input:  File hp ng (PDF/Word/nh)
Output: Bo co ri ro +  xut sa i

Chc nng:
├── Pht hin iu khon vi phm php lut
├── Highlight iu khon bt li
├── Kim tra thiu st (iu khon bt buc)
├── So snh vi template chun
├──  xut sa i c th
├── Chm im ri ro (0-100)
└── To redline version (markup thay i)
```

### Module 3: CONSULT (T vn)
**Thay th:** Lut s t vn, hotline php l
```
Input:  Cu hi php l (text/voice)
Output: Cu tr li + trch dn iu lut c th

Chc nng:
├── Q&A php lut 37+ lnh vc
├── Trch dn iu lut chnh xc
├── Phn tch tnh hung c th
├── Gi  hnh ng tip theo
├── Lch s t vn (audit trail)
└── Multi-language (VN/EN/CN/KR/JP)
```

### Module 4: LIBRARY (Th vin)
**Thay th:** T sch php lut, dch v tra cu
```
├── 600+ vn bn php lut VN (Lut, N, TT)
├── Template library (50+ mu vn bn)
├── Smart search (semantic + keyword)
├── Cross-reference (lut lin quan)
├── Version tracking (lut sa i)
├── Bookmark & highlight
└── Auto-update khi lut mi ban hnh
```

### Module 5: COMPLY (Tun th)
**Thay th:** Kim ton php l
```
Input:  Thng tin doanh nghip (ngnh, rule m, hot ng)
Output: Checklist tun th + cnh bo vi phm

Chc nng:
├── Compliance checklist theo ngnh
├── Deadline nhc nh (bo co thu, BHXH, PCCC)
├── Scanning ni rule vs lut hin hnh
├── Alert khi lut mi nh hng DN
└── Bo co tun th regulation k
```

### Module 6: MANAGE (Qun l)
**Thay th:** T h s, Excel tracking
```
├── Kho vn bn DN (upload, phn loi, search)
├── Tracking hp ng (ht hn, gia hn)
├── Qun l phin bn (ai sa, khi no)
├── Workflow ph duyt (draft → review → approve)
├── Nhc nh deadline (hp ng sp ht, giy php ht hn)
└── Bo co tng hp (bao nhiu H, trng thi)
```

### Module 7: BATCH (X l hng lot)
**Thay th:** Admin/HR son hng trm HL
```
Input:  Template + Excel data (tn, lng, v tr...)
Output: Hng lot vn bn hon chnh

Use cases:
├── 500 HL cho cng nhn mi (HRVN!)
├── 200 ph lc gia hn
├── 100 rulet regulation tng lng
├── 50 thng bo ngh vic
└── Batch export Word/PDF
```

### Module 8: API (Tch hp)
```
REST API + WebSocket + SDK
├── Tch hp vo ERP/HRM hin c
├── Webhook events (H ht hn, lut mi)
├── Embeddable chat widget
├── Mobile SDK (iOS/Android)
└── Zapier / n8n integration
```

---

## 3. System Architecture v2

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   Web    │ │  Chat    │ │  Mobile  │ │  API     │           │
│  │Dashboard │ │ Widget   │ │  App     │ │ Direct   │           │
│  │(Next.js) │ │(Embed)   │ │(Future)  │ │(REST)    │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼─────────────┼────────────┼─────────────┼────────────────┘
        │             │            │             │
        └─────────────┴──────┬─────┴─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│                                                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────────┐   │
│  │   Auth    │ │   Rate    │ │  Billing  │ │   Request      │   │
│  │ (Supabase │ │  Limiter  │ │  Meter    │ │   Router       │   │
│  │  + API    │ │  (Redis)  │ │           │ │                │   │
│  │  Keys)    │ │           │ │           │ │                │   │
│  └───────────┘ └───────────┘ └───────────┘ └────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR LAYER                             │
│                   (FastAPI + LangGraph)                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              INTENT ROUTER                               │     │
│  │  "Son hp ng lao ng" → DRAFT agent                │     │
│  │  "Review file ny" → REVIEW agent                       │     │
│  │  "Thai sn bao lu?" → CONSULT agent                   │     │
│  │  "To 500 HL t Excel" → BATCH agent                 │     │
│  │  "Cng ty ti cn tun th g?" → COMPLY agent         │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌────────────────── AGENT POOL ──────────────────────────┐     │
│  │                                                        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │  DRAFT   │ │  REVIEW  │ │ CONSULT  │ │  COMPLY  │  │     │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  │                                                        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐               │     │
│  │  │  BATCH   │ │ LIBRARY  │ │  MANAGE  │               │     │
│  │  │  Agent   │ │  Agent   │ │  Agent   │               │     │
│  │  └──────────┘ └──────────┘ └──────────┘               │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌────────────────── SHARED SERVICES ────────────────────┐     │
│  │                                                        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │Citation  │ │Halluc.   │ │ Template │ │ Document │  │     │
│  │  │Verifier  │ │Guard     │ │ Engine   │ │ Builder  │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │     │
│  │                                                        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐               │     │
│  │  │ Context  │ │ Compliance│ │ Export   │               │     │
│  │  │ Manager  │ │ Checker  │ │ Service  │               │     │
│  │  └──────────┘ └──────────┘ └──────────┘               │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────────┬────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   RAG ENGINE     │  │   LLM LAYER      │  │   TOOL LAYER     │
│                  │  │                  │  │                  │
│ Hybrid Search    │  │ Claude Sonnet    │  │ OCR (Surya)      │
│ (pgvector +      │  │ (primary)        │  │ PDF Parser       │
│  full-text)      │  │                  │  │ DOCX Generator   │
│                  │  │ Claude Haiku     │  │ PDF Generator    │
│ Reranker         │  │ (fast tasks)     │  │ Excel Reader     │
│                  │  │                  │  │ Template Render  │
│ Context Builder  │  │ Gemini Flash     │  │ E-Sign (future)  │
│                  │  │ (batch/cheap)    │  │ Web Search       │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUPABASE LAYER                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL                              │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │  Tenants    │  │  Law DB      │  │  pgvector        │  │   │
│  │  │  (companies │  │  (636+ docs) │  │  (embeddings)    │  │   │
│  │  │  users,     │  │              │  │                  │  │   │
│  │  │  docs, H)  │  │  Lut, N,  │  │  law_chunks      │  │   │
│  │  │             │  │  TT, Q     │  │  company_chunks  │  │   │
│  │  │  RLS        │  │              │  │  template_chunks │  │   │
│  │  │  isolated   │  │  PUBLIC READ │  │                  │  │   │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐     │
│  │  Auth    │  │ Storage  │  │ Realtime │  │  Edge        │     │
│  │ (Users + │  │ (Docs,   │  │ (Chat,   │  │  Functions   │     │
│  │ API Keys)│  │ exports) │  │ notify)  │  │  (webhooks)  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Document Generation Engine (Core Innovation)

```
┌─────────────────────────────────────────────────────────────────┐
│               DOCUMENT GENERATION ENGINE                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                 TEMPLATE SYSTEM                            │   │
│  │                                                           │   │
│  │  Templates are NOT static Word files.                     │   │
│  │  They are INTELLIGENT SCHEMAS:                            │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────┐          │   │
│  │  │  Template: "hop_dong_lao_dong"               │          │   │
│  │  │                                             │          │   │
│  │  │  Sections:                                  │          │   │
│  │  │  ├── header (company info, date, number)    │          │   │
│  │  │  ├── parties (employer + employee info)     │          │   │
│  │  │  ├── position (job title, department)       │          │   │
│  │  │  ├── term (duration, start date)            │          │   │
│  │  │  ├── salary (base, allowance, bonus)        │          │   │
│  │  │  ├── working_hours (schedule, overtime)     │          │   │
│  │  │  ├── insurance (BHXH, BHYT, BHTN)           │          │   │
│  │  │  ├── leave (annual, sick, maternity)        │          │   │
│  │  │  ├── obligations (employer + employee)      │          │   │
│  │  │  ├── termination (conditions, notice)       │          │   │
│  │  │  ├── dispute (resolution method)            │          │   │
│  │  │  └── signatures                             │          │   │
│  │  │                                             │          │   │
│  │  │  Required by law: [term, salary, insurance] │          │   │
│  │  │  Legal refs: [iu 21-24 BLL 2019]        │          │   │
│  │  │  Compliance rules: [max 36 months, ...]     │          │   │
│  │  └─────────────────────────────────────────────┘          │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                 GENERATION PIPELINE                        │   │
│  │                                                           │   │
│  │  ① Collect Variables                                      │   │
│  │  ┌─────────────────────────────────┐                      │   │
│  │  │ Interactive Q&A or API params:  │                      │   │
│  │  │ - company_name: "HRVN"          │                      │   │
│  │  │ - employee_name: "Nguyn Vn A" │                      │   │
│  │  │ - position: "Cng nhn sn xut"│                      │   │
│  │  │ - salary: 6500000               │                      │   │
│  │  │ - term_months: 12               │                      │   │
│  │  └─────────────────────────────────┘                      │   │
│  │                    │                                      │   │
│  │                    ▼                                      │   │
│  │  ② Validate & Enrich                                     │   │
│  │  ┌─────────────────────────────────┐                      │   │
│  │  │ - Salary >= minimum wage? ✅     │                      │   │
│  │  │ - Term <= 36 months? ✅          │                      │   │
│  │  │ - Required fields present? ✅    │                      │   │
│  │  │ - Auto-calculate BHXH rates     │                      │   │
│  │  │ - Auto-add required clauses     │                      │   │
│  │  └─────────────────────────────────┘                      │   │
│  │                    │                                      │   │
│  │                    ▼                                      │   │
│  │  ③ Generate with LLM                                     │   │
│  │  ┌─────────────────────────────────┐                      │   │
│  │  │ Template schema + variables     │                      │   │
│  │  │ + relevant law articles         │                      │   │
│  │  │ + company custom rules          │                      │   │
│  │  │         │                       │                      │   │
│  │  │         ▼                       │                      │   │
│  │  │    Claude Sonnet                │                      │   │
│  │  │         │                       │                      │   │
│  │  │         ▼                       │                      │   │
│  │  │  Complete document (markdown)   │                      │   │
│  │  └─────────────────────────────────┘                      │   │
│  │                    │                                      │   │
│  │                    ▼                                      │   │
│  │  ④ Compliance Check                                      │   │
│  │  ┌─────────────────────────────────┐                      │   │
│  │  │ Verify generated doc against:   │                      │   │
│  │  │ - Relevant law articles         │                      │   │
│  │  │ - Template required sections    │                      │   │
│  │  │ - Company-specific rules        │                      │   │
│  │  │ - Common legal pitfalls         │                      │   │
│  │  └─────────────────────────────────┘                      │   │
│  │                    │                                      │   │
│  │                    ▼                                      │   │
│  │  ⑤ Export                                                │   │
│  │  ┌─────────────────────────────────┐                      │   │
│  │  │ Markdown → DOCX (python-docx)  │                      │   │
│  │  │ Markdown → PDF (weasyprint)    │                      │   │
│  │  │ With: company logo, formatting │                      │   │
│  │  │       page numbers, headers    │                      │   │
│  │  │       signature blocks         │                      │   │
│  │  └─────────────────────────────────┘                      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Batch Processing Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                  BATCH PROCESSING ENGINE                         │
│          "To 500 HL trong 10 pht"                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Input: Excel/CSV + Template                              │   │
│  │                                                           │   │
│  │  Excel columns mapping:                                   │   │
│  │  ┌──────────────────────────────────────────────────┐     │   │
│  │  │ H tn    │ Date of Birth │ CCCD        │ V tr    │     │   │
│  │  │ Nguyn A  │ 01/01/90  │ 079190xxx  │ CN sn xut│     │   │
│  │  │ Trn B    │ 15/03/95  │ 052195xxx  │ QC         │     │   │
│  │  │ ...       │ ...       │ ...        │ ...        │     │   │
│  │  │ (500 rows)│           │            │            │     │   │
│  │  └──────────────────────────────────────────────────┘     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Processing Pipeline:                                     │   │
│  │                                                           │   │
│  │  Row 1 ──→ Validate ──→ Generate ──→ Check ──→ DOCX  ─┐  │   │
│  │  Row 2 ──→ Validate ──→ Generate ──→ Check ──→ DOCX  ─┤  │   │
│  │  Row 3 ──→ Validate ──→ Generate ──→ Check ──→ DOCX  ─┤  │   │
│  │  ...                                                  ─┤  │   │
│  │  Row N ──→ Validate ──→ Generate ──→ Check ──→ DOCX  ─┤  │   │
│  │                                                        │  │   │
│  │  Parallel processing: 10-20 concurrent (Celery workers) │  │   │
│  │  LLM: Use Gemini Flash for batch (cheaper, fast enough) │  │   │
│  └──────────────────────────────────────────────────────┬──┘   │
│                                                        │       │
│                                                        ▼       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Output:                                                  │   │
│  │  ├── /batch_001/HDLD_NguyenVanA.docx                     │   │
│  │  ├── /batch_001/HDLD_TranVanB.docx                       │   │
│  │  ├── /batch_001/...                                       │   │
│  │  ├── /batch_001/SUMMARY.xlsx (tracking sheet)             │   │
│  │  └── /batch_001/ALL.zip (download all)                    │   │
│  │                                                           │   │
│  │  Summary: 500 created, 498 OK, 2 warnings                │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Template Library Architecture

```
Template Categories:
│
├── 📁 Hp ng (Contracts)
│   ├── hop_dong_lao_dong (HL xc regulation/khng xc regulation time hn)
│   ├── hop_dong_thu_viec (H th vic)
│   ├── hop_dong_dich_vu (H dch v)
│   ├── hop_dong_mua_ban (H mua bn hng ha)
│   ├── hop_dong_thue (H thu mt bng/thit b)
│   ├── hop_dong_hop_tac (H hp tc kinh doanh)
│   ├── hop_dong_dai_ly (H i l/phn phi)
│   ├── hop_dong_vay (H vay vn)
│   ├── hop_dong_gia_cong (H gia cng)
│   └── hop_dong_nhuong_ruleen (H nhng rulen)
│
├── 📁 Ph lc (Appendices)
│   ├── phu_luc_gia_han (Gia hn H)
│   ├── phu_luc_sua_doi (Sa i iu khon)
│   ├── phu_luc_bo_sung (B sung iu khon)
│   ├── phu_luc_thanh_ly (Thanh l H)
│   └── phu_luc_cham_dut (Chm dt H)
│
├── 📁 Quyt regulation (Decisions)
│   ├── ruleet_dinh_tuyen_dung (Tuyn dng)
│   ├── ruleet_dinh_bo_nhiem (B nhim)
│   ├── ruleet_dinh_tang_luong (Tng lng)
│   ├── ruleet_dinh_ky_luat (K lut)
│   ├── ruleet_dinh_sa_thai (Sa thi)
│   ├── ruleet_dinh_nghi_viec (Cho ngh vic)
│   ├── ruleet_dinh_thuyen_chuyen (Thuyn chuyn)
│   └── ruleet_dinh_cu_di_cong_tac (C i cng tc)
│
├── 📁 Ni rule & Quy ch (Policies)
│   ├── noi_rule_lao_dong (Ni rule lao ng)
│   ├── rule_che_luong (Quy ch lng thng)
│   ├── rule_che_tai_chinh (Quy ch ti chnh)
│   ├── rule_trinh_tuyen_dung (Quy trnh tuyn dng)
│   ├── rule_trinh_dao_tao (Quy trnh o to)
│   └── thoa_uoc_lao_dong (Tha c LTT)
│
├── 📁 Cng vn & n t (Correspondence)
│   ├── cong_van (Cng vn)
│   ├── giay_uy_ruleen (Giy y rulen)
│   ├── don_xin_nghi (n xin ngh php)
│   ├── don_khieu_nai (n khiu ni)
│   ├── thu_moi (Th mi)
│   └── thong_bao (Thng bo)
│
├── 📁 Bin bn (Minutes)
│   ├── bien_ban_hop (Bin bn hp)
│   ├── bien_ban_giao_nhan (Bin bn giao nhn)
│   ├── bien_ban_vi_pham (Bin bn vi phm)
│   ├── bien_ban_kiem_tra (Bin bn kim tra)
│   └── nghi_ruleet (Ngh rulet)
│
└── 📁 Bo co (Reports)
    ├── bao_cao_bhxh (Bo co BHXH)
    ├── bao_cao_thue_tncn (Bo co thu TNCN)
    ├── bao_cao_lao_dong (Bo co lao ng)
    └── bao_cao_pccc (Bo co PCCC)

Template Schema (JSON):
{
  "id": "hop_dong_lao_dong",
  "name": "Hp ng Lao ng",
  "category": "contracts",
  "version": "2.0",
  "legal_basis": ["iu 13-24, BLL 2019", "N 145/2020/N-CP"],
  "variables": [
    {"key": "company_name", "label": "Company Name", "type": "text", "required": true},
    {"key": "company_address", "label": "a ch", "type": "text", "required": true},
    {"key": "company_tax_code", "label": "Tax Code", "type": "text", "required": true},
    {"key": "representative", "label": "Ngi i din", "type": "text", "required": true},
    {"key": "representative_title", "label": "Position", "type": "text", "required": true},
    {"key": "employee_name", "label": "H tn NL", "type": "text", "required": true},
    {"key": "employee_dob", "label": "Date of Birth", "type": "date", "required": true},
    {"key": "employee_cccd", "label": "S CCCD", "type": "text", "required": true},
    {"key": "employee_address", "label": "a ch NL", "type": "text", "required": true},
    {"key": "position", "label": "V tr", "type": "text", "required": true},
    {"key": "department", "label": "B phn", "type": "text"},
    {"key": "work_location", "label": "a im lm vic", "type": "text", "required": true},
    {"key": "contract_type", "label": "Loi H", "type": "enum", "options": ["definite", "indefinite", "seasonal"], "required": true},
    {"key": "term_months", "label": "Thi hn (thng)", "type": "number", "max": 36, "condition": "contract_type == 'definite'"},
    {"key": "start_date", "label": "Ngy bt u", "type": "date", "required": true},
    {"key": "base_salary", "label": "Base Salary", "type": "currency", "required": true, "min": "minimum_wage"},
    {"key": "allowances", "label": "Allowances", "type": "json"},
    {"key": "working_hours", "label": "Gi lm/tun", "type": "number", "max": 48, "default": 48},
    {"key": "probation_days", "label": "Th vic (day)", "type": "number", "max": 180}
  ],
  "sections": [...],
  "compliance_rules": [
    {"rule": "term_months <= 36", "message": "HL xc regulation time hn max maximum 36 thng (iu 22)"},
    {"rule": "base_salary >= minimum_wage", "message": "Lng khng c thp hn level max thiu vng"},
    {"rule": "working_hours <= 48", "message": "Khng qu 48 gi/tun (iu 105)"},
    {"rule": "probation_days <= 180", "message": "Th vic max maximum 180 day cho v tr qun l (iu 25)"}
  ]
}
```

---

## 7. Compliance Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE ENGINE                             │
│         "Cng ty bn maximumng tun th php lut cha?"             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Company Profile:                                         │   │
│  │  - Ngnh: Sn xut                                        │   │
│  │  - Quy m: 500 NL                                       │   │
│  │  - a bn: Bnh Dng                                    │   │
│  │  - Hot ng: Gia cng in t                            │   │
│  └──────────────────────┬────────────────────────────────────┘   │
│                         │                                       │
│                         ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Auto-Generate Compliance Checklist:                      │   │
│  │                                                           │   │
│  │  📋 Lao ng                                             │   │
│  │  ├── ✅ HL cho tt c NL                              │   │
│  │  ├── ✅ Ni rule lao ng ng k S LTBXH               │   │
│  │  ├── ⚠️ Tha c LTT (>10 NL → bt buc)             │   │
│  │  ├── ✅ Bo co lao ng 6 thng/nm                     │   │
│  │  └── ❌ Quy ch dn ch c s                            │   │
│  │                                                           │   │
│  │  📋 BHXH/BHYT/BHTN                                       │   │
│  │  ├── ✅ ng BHXH cho NL c HL ≥ 1 thng             │   │
│  │  ├── ⚠️ Khai bo tng/gim L ng hn                  │   │
│  │  └── ✅ Bo co BHXH regulation k                             │   │
│  │                                                           │   │
│  │  📋 An ton lao ng                                     │   │
│  │  ├── ✅ Hun luyn ATVSL                                │   │
│  │  ├── ❌ Khm sc khe regulation k (iu 21 Lut ATVSL)      │   │
│  │  ├── ⚠️ Khai bo tai nn L                              │   │
│  │  └── ✅ nh gi nguy c ri ro                           │   │
│  │                                                           │   │
│  │  📋 PCCC                                                 │   │
│  │  ├── ✅ Giy chng nhn PCCC                              │   │
│  │  ├── ⚠️ Kim tra h thng PCCC regulation k                   │   │
│  │  └── ✅ Tp hun PCCC hng nm                            │   │
│  │                                                           │   │
│  │  📋 Thu                                                 │   │
│  │  ├── ✅ Khai thu GTGT hng thng/qu                    │   │
│  │  ├── ✅ Quyt ton thu TNDN                             │   │
│  │  └── ✅ Quyt ton thu TNCN cho NL                     │   │
│  │                                                           │   │
│  │  📋 Mi trng                                           │   │
│  │  ├── ⚠️ Giy php x thi (sn xut)                    │   │
│  │  ├── ✅ nh gi tc ng mi trng                      │   │
│  │  └── ❌ Bo co BVMT regulation k                             │   │
│  │                                                           │   │
│  │  Score: 72/100 | Issues: 3 critical, 5 warnings           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Deadline Calendar:                                       │   │
│  │                                                           │   │
│  │  📅 15/03 — Np bo co BHXH thng 2                     │   │
│  │  📅 20/03 — Khai thu GTGT thng 2                       │   │
│  │  📅 30/03 — Quyt ton thu TNDN 2025                    │   │
│  │  📅 15/04 — Bo co lao ng Q1                          │   │
│  │  📅 30/06 — Khm sc khe regulation k                        │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Contract Lifecycle Management

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTRACT LIFECYCLE                                  │
│                                                                 │
│  ┌─────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌──────┐  │
│  │Draft│───▶│Review  │───▶│Approve │───▶│Active  │───▶│Expire│  │
│  │     │    │        │    │        │    │        │    │      │  │
│  └─────┘    └────────┘    └────────┘    └───┬────┘    └──────┘  │
│    AI          AI           Human          │                    │
│  generates   checks       approves         │                    │
│                                            │                    │
│                              ┌─────────────┤                    │
│                              │             │                    │
│                              ▼             ▼                    │
│                         ┌────────┐    ┌────────┐               │
│                         │Amend   │    │Renew   │               │
│                         │(Ph lc)│    │(Gia hn)│               │
│                         └────────┘    └────────┘               │
│                                                                 │
│  Tracking Dashboard:                                            │
│  ├── 245 Active contracts                                       │
│  ├── 12 Expiring in 30 days ⚠️                                  │
│  ├── 3 Pending review                                           │
│  ├── 1 Compliance issue 🔴                                      │
│  └── Last created: 2 hours ago                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Pricing Model (Updated)

### Pricing Philosophy: 
> **R hn 90% so vi thu lut s, nhng t hn chatbot thun ty**
> V chng ta **TO ra gi tr** (vn bn), khng ch tr li cu hi

| Plan | Gi/thng | Bao gm | Target |
|---|---|---|---|
| **Starter** | 2.000.000 | 20 docs + 100 Q&A + 5 reviews | SME < 20 NL |
| **Business** | 5.000.000 | 100 docs + 500 Q&A + 20 reviews + compliance | SME 20-100 NL |
| **Enterprise** | 15.000.000 | Unlimited docs + Q&A + batch + API + SLA | DN 100+ NL |
| **Custom** | Tha thun | White-label, dedicated, training | Tp on |

### Add-ons:
- Batch processing (500+ docs): 500.000/batch
- Custom template: 2.000.000/template
- Compliance audit: 3.000.000/ln
- API integration support: 5.000.000 setup

### Actual Cost Comparison:
| Hng mc | Truyn thng | Legal AI Platform |
|---|---|---|
| Son 1 HL | 500K-2tr (lut s) | ~10K (AI) |
| Review 1 H | 2-5tr | ~50K |
| Ni rule L | 5-15tr | ~200K |
| Hire Legal Staff | 15-25tr/thng | 5tr/thng (Business plan) |
| Consult 1 question | 200-500K | ~10K |
| 500 HL batch | 250tr+ (lut s) | 500K |

---

## 10. Development Roadmap (Updated)

### Phase 1: Foundation (Week 1-4)
```
├── Supabase setup + full schema migration
├── FastAPI scaffold + auth + rate limiting
├── Law data pipeline (HuggingFace UTS_VLC → pgvector)
├── RAG engine (hybrid search + reranker)
├── Legal Q&A agent (CONSULT module)
└── Basic API endpoints
```

### Phase 2: Document Engine (Week 5-8)
```
├── Template schema system
├── Document generation pipeline
├── 10 core templates (HL, Q, Ni rule...)
├── DOCX/PDF export (python-docx, weasyprint)
├── Contract review agent (REVIEW module)
├── DRAFT module API endpoints
└── HRVN beta test
```

### Phase 3: Batch + Management (Week 9-12)
```
├── Batch processing engine (Celery workers)
├── Excel import → batch document generation
├── Document management (upload, search, track)
├── Contract lifecycle tracking
├── Compliance engine (basic checklist)
├── Usage tracking + billing
└── Web dashboard (Next.js)
```

### Phase 4: Scale + Launch (Week 13-16)
```
├── Embeddable chat widget
├── Webhook events
├── Complete template library (50+ templates)
├── Advanced compliance (deadline calendar)
├── Mobile-responsive dashboard
├── Landing page + pricing page
├── Public launch
└── First paying customers
```
