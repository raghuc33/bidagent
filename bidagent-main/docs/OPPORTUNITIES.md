# BidAgent — Feature Opportunities

Tools and features that would accelerate the bid writing process, organized by the stage of the bid lifecycle they address.

---

## Stage 1: Understanding the Tender

| Feature | Description | Status |
|---------|-------------|--------|
| Tender Summarizer | Generate a 1-page brief: what they want, key dates, evaluation criteria, deal-breakers | Not built |
| Requirements Extractor | Parse every "shall", "must", "should" into a compliance checklist automatically | **Built** (compliance_check tool) |
| Question Mapper | Map each question to its scoring weight so the user knows where to focus effort | Not built |
| Clarification Drafter | Draft clarification questions to submit to the buyer before the deadline | Not built |
| Red Flag Scanner | Flag deal-breakers: "This tender requires SC clearance — do we have it?" | Partial (go/no-go) |

---

## Stage 2: Gathering Evidence

| Feature | Description | Status |
|---------|-------------|--------|
| Smart Evidence Library | Tag past case studies by skill, sector, client, value — not just keyword search | Not built |
| Evidence Matcher | "For Essential Skills #3, here are your 3 strongest case studies, ranked by relevance" | Partial (search_knowledge_base tool) |
| Gap Identifier | "You have no evidence for 'legacy IDMS migration' — write from scratch or get an SME" | **Built** (analyze_evidence_gaps tool) |
| CV / Team Builder | Pull relevant experience from team member profiles and auto-format for the bid | Not built |
| Competitor Intel | "Based on public contract data, here's who else is likely bidding and their strengths" | Not built |

---

## Stage 3: Writing the Response

| Feature | Description | Status |
|---------|-------------|--------|
| Scoring Criteria Overlay | Show the evaluation criteria next to each section while writing — highlight which criteria are met and which are missing | Not built |
| Win Theme Injector | Maintain 2-3 win themes across all sections (e.g. "cost savings", "innovation") and ensure they appear consistently | Not built |
| Evidence Citation Manager | Drag evidence into a section, auto-formats with page/project references | Not built |
| Real-time Compliance Tracker | Live checklist: "Section 3 mentions 4 of 6 required keywords — missing: 'knowledge transfer', 'TUPE'" | Not built |
| Template Library | Reusable boilerplate for common sections (social value, GDPR, security, pricing methodology) | Not built |
| Generate All Sections | Auto-generate all sections after upload in one click | **Built** |
| Word Count Enforcer | Hard stop at 250 words (target: 240-249) via squeeze tool | **Built** (squeeze_word_count tool) |
| Tone Stylist | Rewrite for UK public sector tone: authoritative, collaborative, outcome-focused | **Built** (restyle_tone tool) |

---

## Stage 4: Review & Quality

| Feature | Description | Status |
|---------|-------------|--------|
| Red Team Scorer | Score every section 0-100 independently against evaluation criteria | **Built** (score_against_rubric tool) |
| Cross-Section Consistency Check | "Section 2 says 'team of 8' but Section 4 says 'team of 6'" — flag contradictions | Not built |
| Compliance Matrix | Auto-generate a matrix showing which requirement is addressed where | **Built** |
| Readability Score | Flesch-Kincaid or similar — buyers scan, not read. Keep it accessible | Not built |
| Claim Verification | "You claim '95% uptime' — is this in your evidence? If not, flag it as unsubstantiated" | Not built |
| Review Workflow | Assign sections to reviewers, track review status, manage feedback loops | Not built |
| Version History | Track changes per section — roll back to previous drafts | Not built |

---

## Stage 5: Formatting & Submission

| Feature | Description | Status |
|---------|-------------|--------|
| DOCX Export | Formatted Word document matching the buyer's template | Not built (markdown only) |
| Portal-Ready Formatter | Auto-format for specific portals (Digital Marketplace, Contracts Finder, Jaggaer) | Not built |
| Attachment Manager | Track required attachments (certificates, insurance, accounts) with checklist | Not built |
| Submission Checklist | Final pre-flight: "All sections complete? Attachments present? Word counts OK? Signed?" | Not built |
| PDF Generator | Combined bid pack as a single formatted PDF | Not built |

---

## Stage 6: Post-Submission

| Feature | Description | Status |
|---------|-------------|--------|
| Win/Loss Tracker | Record outcome and buyer feedback for each bid | Not built |
| Analytics Dashboard | Win rate by sector, average score, common weaknesses | Not built |
| Lessons Learned | Feed buyer feedback back into the scoring rubric to improve future bids | Not built |
| Reuse Index | Which sections from this bid can be reused for future tenders | Not built |

---

## Additional Agent Tools

Tools the chat agent could invoke beyond what's currently built:

| Tool | Description | Status |
|------|-------------|--------|
| search_knowledge_base | Semantic search across uploaded docs | **Built** |
| generate_draft | RAG-powered bid draft (~400 words) | **Built** |
| squeeze_word_count | Rewrite to 240-249 words | **Built** |
| score_against_rubric | Score 0-100 with breakdown | **Built** |
| analyze_evidence_gaps | Identify missing evidence | **Built** |
| restyle_tone | UK public sector tone adjustment | **Built** |
| compliance_check | Extract requirements and check coverage | **Built** |
| generate_all_sections | Batch-generate all remaining sections | Not built (as tool) |
| copy_style_from | Match tone/structure of a reference winning bid | Not built |
| find_similar_past_bids | Search KB for previous bids on similar topics | Not built |
| insert_evidence | Find and insert specific evidence at the right spot in a draft | Not built |
| compare_versions | Show diff between current and previous draft | Not built |
| summarize_tender | Generate a 1-paragraph summary of the whole tender | Not built |
| check_formatting | Validate bullet points, numbering, heading structure | Not built |
| translate_jargon | Replace technical jargon with plain English | Not built |
| add_metrics | Suggest quantifiable metrics to strengthen claims | Not built |
| cross_reference_sections | Check for contradictions between sections | Not built |

---

## Priority Recommendations

If building the next 5 features, these would have the highest impact on bid win rates:

1. **Scoring Criteria Overlay** — Show evaluators' criteria beside each section while editing. This is the #1 reason bids score poorly: writers don't address the actual criteria.

2. **DOCX Export** — Nobody submits markdown. Every buyer wants Word format. Table stakes for a real product.

3. **Cross-Section Consistency Check** — Contradictions between sections are an instant red flag for evaluators.

4. **Submission Checklist** — 15% of bids are disqualified for non-technical reasons (missing signature, wrong format, over word count). This is free points.

5. **Template Library** — Common sections like social value, GDPR, security are 80% reusable across bids. Pre-built templates save hours.
