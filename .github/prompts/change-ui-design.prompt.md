---
mode: agent
description: "Redesign or restyle the UI — learn CSS theming, layout, and visual design"
---

# Change the UI Design

Owen wants to change how the app looks — colors, layout, typography, or overall theme. Guide him through the CSS design system and how to make visual changes confidently.

## Context

The frontend lives in `static/` with no build step:
- `static/style.css` — Dark theme using CSS custom properties (`:root` variables)
- `static/index.html` — SPA layout with sidebar nav and tab panels
- `static/app.js` — Rendering logic (usually unchanged for pure style updates)

## The CSS Design System

All colors and spacing are controlled by CSS custom properties in `:root`:

```css
:root {
    --bg: #0f0f1a;           /* page background */
    --surface: #1a1a2e;      /* card/panel background */
    --surface-hover: #252540; /* hover states */
    --primary: #6c63ff;      /* accent color (buttons, links) */
    --primary-hover: #5a52d9; /* accent hover */
    --text: #e8e8f0;         /* main text */
    --text-muted: #8888aa;   /* secondary text */
    --success: #4ade80;      /* correct/positive */
    --error: #f87171;        /* wrong/negative */
    --border: #2a2a45;       /* borders and dividers */
}
```

**Key insight:** Change a variable in `:root` and it updates *everywhere* — buttons, cards, backgrounds, text. This is the power of design tokens.

## Guided exercises (pick one or do several):

### 1. Change the color theme
- **Light mode:** Swap dark backgrounds for light ones, dark text for light text
- **Different accent color:** Change `--primary` from purple to blue, green, or orange
- **High contrast:** Make text brighter, borders more visible
- Teach: CSS custom properties, color theory basics, accessibility contrast ratios

### 2. Change the layout
- **Top nav instead of sidebar:** Move navigation from the left column to a horizontal bar
- **Full-width chat:** Make the chat panel wider on large screens
- **Mobile responsive:** Add `@media` queries so it works on phones
- Teach: CSS Grid vs Flexbox, responsive design, breakpoints

### 3. Change typography
- **Import a Google Font:** Add a `<link>` to index.html, update `font-family`
- **Adjust sizing:** Change heading sizes, body text size, line height
- **Math font pairing:** Find fonts that look good alongside KaTeX math rendering
- Teach: Web fonts, `rem` vs `px`, typographic scale

### 4. Add animations and polish
- **Smooth transitions:** Add `transition` to buttons, cards, hover states
- **Message animations:** Messages slide in when they appear
- **Loading states:** Skeleton screens or pulse animations while waiting for AI
- Teach: CSS transitions, `@keyframes`, `animation`, performance (GPU-accelerated properties)

### 5. Redesign a specific component
- **Chat bubbles:** Change shape, alignment, spacing, add avatars
- **Quiz cards:** Redesign the question layout, answer selection style
- **Progress cards:** Add charts, change the progress bar style
- **Scratch pad:** Style the toolbar, add a nicer canvas border
- Teach: Component-scoped CSS, BEM naming, visual hierarchy

## Steps for any UI change:

1. **Identify what to change** — Screenshot or describe the current state and the desired state
2. **Find the CSS** — Use browser DevTools (F12 → Elements → Styles) to find which rules control the element
3. **Make the change in `static/style.css`** — Prefer changing variables in `:root` over hardcoding values
4. **Hard refresh** — Ctrl+Shift+R to bypass the browser cache
5. **Test across all tabs** — Make sure the change looks good in Chat, Quiz, Scratch Pad, and Progress
6. **Check edge cases** — Long messages, empty states, error states, math rendering

## Using Browser DevTools (essential skill):

1. Right-click any element → **Inspect**
2. The **Elements** panel shows the HTML structure
3. The **Styles** panel on the right shows all CSS rules affecting that element
4. You can **edit CSS live** in DevTools to preview changes before editing the file
5. The **Computed** tab shows the final resolved values (useful for inherited properties)

## Teaching moments:
- Why CSS custom properties beat hardcoded colors
- The CSS specificity cascade — how the browser decides which rule wins
- Box model: margin → border → padding → content
- Flexbox for 1D layout, Grid for 2D layout
- Why `rem` units scale better than `px`
- Accessibility: contrast ratios, focus indicators, reduced motion preferences
