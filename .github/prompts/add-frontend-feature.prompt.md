---
mode: agent
description: "Add a new UI feature to the frontend — DOM, CSS, API integration"
---

# Add a Frontend Feature

Owen wants to add a new feature to the web UI. Guide him through the vanilla JS/CSS approach.

## Context

The frontend is in `static/` with no build step:
- `index.html` — SPA shell with sidebar nav and tab panels
- `style.css` — Dark theme using CSS custom properties (`:root` variables)
- `app.js` — Tab routing, API calls, KaTeX/Marked rendering, scratch pad canvas

## Steps to follow:

1. **Plan the UI** — Describe what the feature looks like before writing code
   - Where does it go? (new tab, inside existing tab, modal?)
   - What data does it need from the API?
   - Does it need math rendering? (`renderContent()`)

2. **Add the HTML structure** in `index.html`
   - If it's a new tab: add a `<button class="nav-item">` to the sidebar and a `<section class="panel">` to main
   - Follow the existing class naming conventions
   - Use semantic HTML (section, header, button) not div soup

3. **Style it** in `style.css`
   - Use the existing CSS custom properties: `var(--surface)`, `var(--primary)`, `var(--text)`, etc.
   - Follow the existing patterns for cards, buttons, form fields
   - Explain the CSS — don't just write it

4. **Wire up the JavaScript** in `app.js`
   - Add event listeners
   - Fetch from the API with proper error handling
   - Use `renderContent(text)` for any content that might contain math/markdown
   - Explain the fetch → render → DOM update cycle

5. **Test it end-to-end**
   - Hard-refresh the browser (Ctrl+Shift+R) since files are served statically
   - Check the browser console for errors
   - Test edge cases (empty input, API errors)

## Teaching moments:
- Why vanilla JS instead of React? (simplicity, learning fundamentals)
- How `fetch()` works with async/await
- DOM manipulation basics: `createElement`, `innerHTML`, `textContent`
- CSS custom properties vs hardcoded values
- The `renderContent()` pipeline: Markdown → HTML → KaTeX
