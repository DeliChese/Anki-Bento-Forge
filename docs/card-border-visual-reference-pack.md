# Bento Forge — Card Border Visual Reference Pack

> Status: code-derived draft. Attach the screenshots in the capture checklist before approving a production asset.
>
> Purpose: give an external image or motion generator enough factual visual and technical context to propose a card-border style safely. This document does **not** authorize changing Anki templates or generating an asset automatically.

## 1. Product context

Bento Forge is an Anki add-on for vocabulary and grammar study in Japanese, Chinese, Korean, and English. The border is an optional **decorative overlay** selected in a Workshop, either as a global default or a deck-specific override. It must never compete with the word, meaning, answer input, examples, audio, or study-mode controls.

The same visual family is used on both question and answer sides. A deck may choose a different family; a card itself is never modified to store the choice.

## 2. Facts from the live card contract

| Constraint | Verified contract |
| --- | --- |
| Desktop card width | `.cw` is fluid up to `680px`, with a `1px` native border and rounded corners. |
| Desktop outer spacing | The card is centered with `20px` vertical margin; the review body has `20px 16px` padding. |
| Mobile | At `<=520px`, the card is full width, has `10px` outer margin, and a `14px` radius. |
| Height | Deliberately fluid. Question, answer, grammar, and interactive modes do not have a fixed height. |
| Top region | Header carries level and topic. Do not cover it. |
| Main region | Word/pattern, reading, typed answer, or exercise content. Do not enter it. |
| Answer region | Meaning, audio, usage guide, and up to two example blocks. It can make the answer substantially taller than the question. |
| Interactive regions | Combo mode includes a study-mode bar; word-building and typed-answer modes include controls. Borders must not capture pointer events. |

Sources: `mode/css.py` (`.cw`, `.ch`, `.vb`, `.ir`, `.es`, `.mode-bar`, and the mobile media query), plus `mode/templates/common.py` and `mode/templates/*`.

## 3. Asset architecture — required

Do **not** request or use one full-card bitmap with a fixed rectangular hole. Its safe area will fail as the card grows vertically.

Create a single visual family as a **9-slice border source**:

```text
┌───────────┬─────────────────────┬───────────┐
│ corner TL │     top edge        │ corner TR │
├───────────┼─────────────────────┼───────────┤
│ left edge │ transparent centre  │ right edge│
├───────────┼─────────────────────┼───────────┤
│ corner BL │    bottom edge      │ corner BR │
└───────────┴─────────────────────┴───────────┘
```

- Master concept canvas: `2048 x 2048px`, genuine alpha transparency.
- Corner art lives within the outer `12.5%` of both axes; each edge occupies only its outer `8%` strip.
- The entire interior must be transparent. Do not paint a translucent wash, texture, particle, shadow, or glow across it.
- Edge artwork must remain visually continuous when stretched or tiled.
- Final exported files will be cut into 4 corners + 4 repeatable/stretchable edges. The centre is no file and must remain transparent.
- The implementation will use a non-interactive overlay (`pointer-events: none`) below controls and content. The asset must not include its own text or controls.

## 4. Visual and accessibility locks

- Art direction: an animated-avatar-frame feeling — polished, collectible, soft energy — but still calm enough for repeated learning.
- No characters, faces, mascots, logos, letters, symbols, level labels, buttons, badges, or watermarks.
- Avoid thin high-frequency ornament, sharp spikes, metallic glare over text, confetti, or particles that travel into the centre.
- Must read on both light cards and `.nightMode` cards. Keep the strongest highlights on the outermost edge.
- The static frame must look complete. Motion is implemented separately as a slow CSS shimmer/glow (4–6 seconds), never as an autoplay video/GIF.
- Respect `prefers-reduced-motion`: motion can be disabled without making the asset look unfinished.

## 5. Screenshot capture checklist

Before asking an AI generator to produce the approved asset, attach a contact sheet of these screenshots. Use a disposable sample note only; do not expose personal study data.

1. English Combo, QA question, desktop.
2. The same English Combo card, QA answer, with two examples and a usage guide, desktop.
3. A Word Building or typed-answer card, desktop.
4. One Japanese or Chinese card with the longest expected word/reading, desktop.
5. A Combo question and answer at mobile width (`<=520px`).
6. One representative night-mode card.

For each screenshot, add a thin red outline around the existing `.cw` boundary. The AI may use screenshots as **layout reference only**; it must not copy text or UI elements into the asset.

## 6. Reusable generator handoff

Paste this after attaching the contact sheet. It is intentionally a two-stage request, so style selection happens before rendering.

```text
You are proposing a decorative border asset for Bento Forge, an Anki learning-card add-on.
The attached screenshots are factual layout references. Preserve their card boundary and keep every UI/content region unobstructed.

The asset is a transparent 9-slice overlay, not a card background. It must work for fluid-height front and back cards, desktop and mobile, light and night mode.
The centre is fully transparent. Corner art must stay within the outer 12.5% of each axis; edge art must stay within the outer 8% strip.
No text, logos, icons, characters, controls, opaque background, particles in the centre, flashing, or GIF/video output.
Motion, if approved later, will be a subtle 4–6 second CSS shimmer; the static source must already look finished.

First response only:
1. State any assumptions.
2. Propose exactly four distinct visual styles, S1–S4.
3. For each: name, mood, palette, corner motif, edge treatment, and recommended CSS motion.
4. Recommend one style for repeated study.
5. Stop. Do not generate an image or an image-generation prompt.

Wait until I reply exactly `CHỌN STYLE: S1`, `S2`, `S3`, or `S4`.
```

## 7. Production acceptance gate

An asset is eligible for Workshop integration only when all answers are yes:

- Does it have a genuine transparent centre and no baked-in card background?
- Can its edges be sliced/repeated without seams or distorted motifs?
- Are header, word/pattern, inputs, buttons, meaning, usage guide, examples, and audio all unobscured in the screenshot matrix?
- Does it remain legible and quiet on light and night mode?
- Does static artwork still look intentional with motion disabled?
- Is the asset free of text, logo, watermark, and unlicensed reference material?

