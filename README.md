# The Unofficial Guide

David Arutyunyan — corpus: `campus_life`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

**Chunk size:** 450 characters — a ceiling, not the usual cut point
**Overlap:** 0 characters

Chunks are cut on **paragraph boundaries**, and every chunk carries its
document's title line. The function is `chunker.py::split_documents`.

**What the starter did.** `fallback_split` cut fixed 800-character windows with
120 characters of overlap. On `campus_life` it never cut anything: the longest
document is 549 characters, so all 88 documents came out as 88 chunks. One post
about a dorm was a single chunk covering its build year, its best feature, its
worst feature, the laundry prices and the noise — five unrelated facts in one
retrievable unit.

**What I changed and why.** These documents already mark their own topic
boundaries with blank lines. Measuring the corpus: 88 documents contain 271
paragraph blocks — exactly one title block each plus 183 body paragraphs,
median 112 characters. The authors put one thought in each paragraph, so
paragraphs are the natural unit and splitting on them needs no guesswork.

The title has to travel with each piece, and that is the part I would have got
wrong without looking at the documents. Seven buildings each have a laundry
paragraph, and they differ only in price. Stripped of its heading, *"Machines
take $1.50 wash, $1.25 dry, coin or card"* could be any of the seven, and a
question naming a building could not retrieve the right one. Prepending the
title costs at most 47 characters — the longest title in the corpus.

**Why 450.** The longest body paragraph is 373 characters and the longest title
is 47; with the blank line between them that is 422. A 450-character ceiling
therefore leaves every real paragraph intact and only fires on something
abnormal, in which case `_split_long` breaks between sentences rather than
mid-word.

**Why no overlap.** Overlap repairs context lost when a cut lands inside a
thought. This chunker only cuts where the author already stopped, and copies
the title onto every chunk, so there is nothing to repair. Overlap here would
duplicate whole paragraphs into neighbouring chunks and make the same text
compete with itself at retrieval.

**Paragraphs shorter than 60 characters** are grouped onto their neighbour so
no chunk is a stub. Only 10 of the 183 body paragraphs fall below that.

**Result:** 88 documents → 173 chunks, averaging 175 characters (shortest 86,
longest 397), against the baseline's 88 chunks averaging 317 (shortest 178,
longest 549).

**Tradeoff discovered.** Chunks are now roughly half the size, so each one
carries less surrounding material. For this corpus that is the right direction
— the facts are one-sentence facts — but on a corpus where an answer spanned
several paragraphs this strategy would cut through it, and overlap would start
to earn its keep.

## Sample Chunks

Five chunks as printed by `python app.py chunks -n 5`, which samples by stride
across the whole corpus rather than letting me pick favourites.

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_cs_340_exams.txt#1` — produced by: `chunker.py::split_documents`

```
CS 340 Databases — assessment

Start the term project in week three, not week eight; everyone learns this the hard way.
```

**Chunk 3** — source: `course_stat_150_exams.txt#0` — produced by: `chunker.py::split_documents`

```
STAT 150 Applied Statistics — assessment

Three equally weighted midterms, no final. No curve, but the lowest midterm is dropped.
```

**Chunk 4** — source: `housing_aldridge_hall.txt#0` — produced by: `chunker.py::split_documents`

```
Aldridge Hall — what it's actually like

I lived here my sophomore year. Built 1968, renovated 2019. Rooms are doubles with a shared bathroom per floor.
```

**Chunk 5** — source: `housing_morrow_house.txt#3` — produced by: `chunker.py::split_documents`

```
Morrow House — what it's actually like

Laundry costs $1.50 wash, $1.25 dry, coin or card. On noise: loud until about 1am on weekends, no enforced quiet hours.
```

All five carry a complete thought and name their own subject without needing a
neighbouring chunk. Chunk 5 is the one the old chunker got wrong: under
`fallback_split` that laundry line sat inside a single 461-character chunk
alongside the building's room layout, its housing-tier price and its damp
problem. The new chunker splits that document into four chunks, one per topic.

## Sample Answer

**Question:** What does it cost to dry a load of laundry in Morrow House?

**Answer:**

```
  (best distance 0.182, cutoff 0.6)

It costs $1.25 to dry a load of laundry in Morrow House.

Sources: housing_morrow_house.txt and housing_morrow_house_laundry.txt

Sources retrieved: housing_aldridge_hall_laundry.txt, housing_innisfree_hall_laundry.txt, housing_morrow_house.txt, housing_morrow_house_laundry.txt, housing_old_brewhouse_laundry.txt

1 model calls this session, 505 tokens (466 in, 39 out)
```

This is the question worth showing, because the prompt it produced contained
four other buildings' laundry paragraphs — Old Brewhouse at $1.50 dry,
Aldridge Hall at $1.50, Innisfree Hall at $1.75 — and the answer still returned
Morrow House's $1.25 and cited the two Morrow House files. Retrieval put both
Morrow documents at ranks 1 and 2 (0.182 and 0.210) ahead of every other
building (0.335 and worse), which is the title prefix in the chunker doing its
job.

**My relevance cutoff:** 0.6, unchanged from the starter default — but now
measured rather than assumed.

I ran my five test questions and the five `OUT_OF_SCOPE` questions and recorded
the best distance for each. The two groups do not overlap anywhere near the
cutoff: covered questions land between 0.180 and 0.364, out-of-scope between
0.825 and 0.923, leaving a gap of 0.46 with nothing in it. 0.6 sits close to
the midpoint of that gap (the true midpoint is 0.594), so it has about 0.23 of
margin on both sides. Any value from roughly 0.37 to 0.82 would score
identically on these ten questions; I kept 0.6 because the midpoint is the
most robust choice for questions I haven't tried, and moving it would have been
a change with no evidence behind it.

| Question | In corpus? | Best distance |
|---|---|---|
| If I drop a course, after which point does it show as a W on my transcript? | yes | 0.2547 |
| How often does the campus shuttle run on weekends? | yes | 0.1799 |
| What time does the library close during reading week? | yes | 0.2192 |
| What does it cost to dry a load of laundry in Morrow House? | yes | 0.1821 |
| What does a meal at Kestrel Commons cost without a meal swipe? | yes | 0.3643 |
| What is the capital of Mongolia? | no | 0.8246 |
| How do I change the oil in a diesel engine? | no | 0.9228 |
| Who won the 1994 World Cup? | no | 0.8859 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8487 |
| How do I write a for loop in Rust? | no | 0.8635 |

All five out-of-scope questions were refused by the gate, and each run reported
`0 model calls this session` — the refusal happens in `gate.py::check` before
`generate.py` is ever reached, so a refused question costs no API quota.

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
