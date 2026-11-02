# V3 presentation readability audit

The user reported small graph labels, hard-to-find cost information, and missing speed/cost colour coding. This audit compares the published v3 presentation with a presentation-only successor. The underlying questions, scores, timing records, cost records and license notices are unchanged.

| Area | Before | After | Evidence |
|---|---:|---:|---|
| Hierarchy | 3/5 | 4/5 | The original overview led with one compressed three-panel graphic. The successor puts the comparison table first, followed by three individually labelled graphs. |
| Typography | 2/5 | 4/5 | Model and value labels were very small when the wide overview was fitted to the page. Separate full-width graphs and larger category-matrix labels make the same values legible. |
| Colour | 2/5 | 4/5 | The original main table had speed backgrounds but no cost background, and its GitHub table lacked speed/cost markers. The successor colours both measures and prints the band names; the GitHub table uses matching colour markers. |
| Spacing | 3/5 | 4/5 | On a 390-pixel viewport the original cost columns were outside the visible area. Mobile cards now keep accuracy, timing and both cost measures together. |
| States | 3/5 | 4/5 | Search and category selection worked before and after. The successor also explicitly reports an empty model search. Loading and network-error states do not apply to the static report. |
| Accessibility | 2/5 | 3/5 | Small chart labels and the off-screen cost columns impeded reading. Larger charts, mobile cards, text labels for colour bands and a visible focus indicator improve access. A comprehensive assistive-technology audit was not performed. |
| Copy | 4/5 | 4/5 | The selection-bias and source-rights caveats remain visible. Known subtotals, estimates, missing charges and unmetered local costs remain qualified. |

Desktop and mobile first-view and overview screenshots were inspected at 1,440 and 390 pixels respectively. The browser could not capture the unusually long original report as a single full-page screenshot, so the relevant sections were inspected separately. Model search, its empty state, category selection and image loading were exercised. Static pages do not have applicable loading or service-error states.

The role colours and coloured square markers are intentional encodings requested by the benchmark owner. They are accompanied by text and a legend. The primary fixes were split comparison graphs, larger category labels, colour-coded total and normalized cost columns, and mobile cards. Broader visual redesign and a comprehensive accessibility audit were outside this targeted correction.
