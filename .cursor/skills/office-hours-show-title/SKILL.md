---
name: office-hours-show-title
description: >-
  Drafts a catchy, argumentative Open Disruption office-hours show title for the
  title slide and Zoom promo from the week's link list. Returns one slide title,
  two alternates, and a one-sentence promo, then saves them to
  weekly-links/YYYY-MM-DD-show-title.md. Use when the user asks for a title
  slide, show title, office-hours headline, weekly promo, or Zoom hook for the
  week's AI news.
---

# Office Hours Show Title

Write a Zoom hook for Open Disruption office hours. Someone scrolling should feel the claim is arguable and that office hours is where the argument happens.

## Workflow

1. Resolve the date: use the date the user names, otherwise the latest `RAW_LINKS/YYYY-MM-DD` file.
2. Read sources in this order:
   - `RAW_LINKS/YYYY-MM-DD` first. Weight the `<HEADLINES>` section over Graphics, Prompt Share, and later sections unless those sections are clearly the week.
   - If `weekly-links/YYYY-MM-DD-headlines.md` exists, prefer those rewritten anchors over scraped page titles.
3. Draft one slide title, two alternates, and one promo sentence using the voice rules below.
4. Reply in chat with that copy.
5. Write (or overwrite) `weekly-links/YYYY-MM-DD-show-title.md` using the save template. Do not touch the links page, the per-link headlines file, the rundown, or any weekly scripts.

## Voice

- Catchy enough to say out loud on a title slide.
- Controversial by framing real items as a claim someone could disagree with. Pick the fight the links support.
- The three title lines poke different nerves. Do not write three phrasings of the same news item.
- Reject neutral headlines (`Anthropic Announces an IPO`, `Everybody Shipped`, `This Week in AI`).

## Shape

- **Slide title:** one short line, ideally under eight words. A second punch is allowed when it makes the argument (`Everybody Shipped. You're Late.`).
- **Alternates:** two full replacements, each a different nerve.
- **Promo:** one sentence, about 30 words. Name the two or three facts that earn the title, then invite people to office hours on Zoom.

## Grounding

Do not invent details the links do not state (who Nvidia's next CEO is, IPO terms, benchmark numbers, scandals). Argue from what the list actually contains.

## Chat reply format

```markdown
**Slide title:** …

**Alternates:**
- …
- …

**Promo:** …
```

## Save template

Write exactly this structure to `weekly-links/YYYY-MM-DD-show-title.md`:

```markdown
# Open Disruption — Show Title
**Date:** YYYY-MM-DD

**Slide title:** …

**Alternates:**
- …
- …

**Promo:** …
```

## Worked example (2026-11-12)

From that week's headlines (Nvidia CEO transition, Claude Fable/Mythos 5.2, Anthropic IPO, Gemini 4, United ban on AI booking bots):

**Slide title:** Your Agent Can't Book a Flight

**Alternates:**
- Anthropic Is Selling the Future
- Everybody Shipped. You're Late.

**Promo:** Frontier models dropped, Anthropic announced an IPO, and Nvidia changed CEOs — while United banned AI from booking flights. Come argue it at office hours on Zoom.
