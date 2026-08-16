# Agent Context Packs

> Status: active  
> Authority: operating policy for repository-aware agents  
> Last verified: 2026-08-16  
> Read when: cấu hình Zoo Code, Repomix hoặc chuyển giao task

## Default pack

Luôn bắt đầu bằng đúng bốn file: `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md` và **một** `SKILL.md` phù hợp. Không nạp source, benchmark, roadmap history hoặc assessment trước khi xác định phạm vi.

## Expand only by evidence

| Loại task | Chỉ thêm sau `rg` | Kiểm chứng tối thiểu |
|---|---|---|
| Bug/UI/TTS nhỏ | Module owner, caller trực tiếp, test gần nhất | Test/smoke theo skill 10 |
| AI/prompt/cache | Skill 02, module AI liên quan, fixture/benchmark đúng feature | Parser/cache/prompt test và benchmark khi output đổi |
| Feature xuyên module | Task contract, các owner trên dependency path, test từng owner | Diff review + test liên quan + smoke nếu mutation Anki |
| Release/compatibility | Skill 11, manifest/build script, release checklist | Artifact và gate trong roadmap |

## Repomix policy

Tạo pack theo vertical slice, không theo thư mục gốc. Pack phải nêu task ID, skill đã đọc và chỉ gồm source/test/document trực tiếp quyết định task. Không đưa các tài liệu `Status: historical` hoặc `Status: frozen` trừ khi task contract giải thích vì sao cần chúng.

Ví dụ task P1-06 chỉ nên bắt đầu với: context mặc định, skill 02 hoặc skill 01, `utils` owner đã được `rg` xác minh, preview/import caller trực tiếp, fixture liên quan và test đó. Thêm `benchmarks/` chỉ khi thay đổi prompt/model/quality gate.

## Handoff rule

Mọi task trung bình/khó, mọi đổi model, hoặc context vượt khoảng một phần ba cửa sổ phải cập nhật [task contract template](../.claude/context/task-contract-template.md). Handoff chỉ ghi quyết định, file/symbol đã xác minh, diff, kiểm chứng và blocker — không dán lại toàn bộ chat hoặc repo summary.
