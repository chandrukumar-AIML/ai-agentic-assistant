# /design-review — Visual & UX Audit

Act as the **Frontend Engineer + UX Reviewer** from AGENTS.md.
Reference: PERSONAS.md for who we're designing for.

## Live Browser Audit

Open each agent page and audit against these dimensions (score 0–10):

### 1. First Impression (0-10)
- Does it feel enterprise and trustworthy?
- Dark design system applied consistently?
- No jarring color inconsistencies?

### 2. Feature Discovery (0-10)
- Workspace wizard appears on first visit?
- Tab groups visible and labelled clearly?
- Search bar accessible when > 8 features?
- Active feature clearly highlighted?

### 3. Form Usability (0-10)
- Workspace pre-fills common fields?
- Labels are clear, placeholders give examples?
- Submit button state (loading / disabled / enabled) correct?
- Error state shown when API fails?

### 4. Result Quality (0-10)
- ResultBox renders markdown properly?
- Tables scroll horizontally on overflow?
- Loading spinner (not ⏳ emoji) shown?
- Result area large enough to read comfortably?

### 5. Mobile Responsiveness (0-10)
- Sidebar collapses on narrow screens?
- Tab pills wrap without breaking layout?
- Forms usable on 375px width?

### 6. Accessibility (0-10)
- Sufficient color contrast (text on surface)?
- Keyboard navigation works?
- No layout shift on load?

### 7. Persona Fit (0-10)
Reference PERSONAS.md:
- Would Priya Sharma (CA) find CA page intuitive?
- Would Rajesh Kumar (ecommerce) navigate CS features?
- Would Kavitha Nair (agency) trust the SM agent?

## Output

For each page (SM / CS / CA / Dashboard / Landing / Login):

```
[Page name]
First Impression: X/10 — [note]
Feature Discovery: X/10 — [note]
Form Usability:    X/10 — [note]
Result Quality:    X/10 — [note]
Responsive:        X/10 — [note]
Accessibility:     X/10 — [note]
Persona Fit:       X/10 — [note]
TOTAL: XX/70

Top 3 fixes for this page:
1. ...
2. ...
3. ...
```

## Fix Priority

After scoring all pages, list fixes in order:
- 🔴 Score < 5 — fix before next deploy
- 🟡 Score 5–7 — fix this sprint
- 🟢 Score 8+ — note for future polish
