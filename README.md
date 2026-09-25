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

This is a question-answering system over `campus_life`, a corpus of 88 short
posts written student-to-student about one university — dining halls, dorms,
courses, and the administrative rules nobody explains properly. It answers
factual questions about those topics: deadlines, prices, opening hours, shuttle
frequencies, laundry costs, how a course is assessed. Every answer is written
only from chunks retrieved out of the corpus, and names the document it came
from, so any claim can be traced back to a file. When nothing in the corpus is
close enough to the question, a relevance gate refuses it before the language
model is called at all, rather than letting the model guess.

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

**1. Getting the environment to build on Windows.** I asked Claude to install
a Python version the course supports and get the starter running. It checked
my machine, found only Python 3.14 installed — which this course's pinned
packages don't support — and installed 3.13. `pip install -r requirements.txt`
then failed part-way through with `Microsoft Visual C++ 14.0 or greater is
required`, while building `chroma-hnswlib`. Rather than tell me to install
multi-gigabyte C++ build tools, Claude queried PyPI for which Python versions
that package actually ships a Windows wheel for, and found there is exactly
one: cp311. Not 3.12, not 3.13. So it installed Python 3.11.9, rebuilt the
virtual environment on it, and `test.py` went to 10 passed / 0 failed with no
compiler involved and no change to any project file. The useful part was that
the first fix attempt was wrong and the diagnosis came from checking the
package index instead of guessing.

**2. Pressure-testing my test questions before I ran any of them.** I asked
Claude to check that each of my five `expects` phrases was actually supported
by the corpus file I claimed it came from. Four checked out. On the fifth — my
STAT 150 question with `expects="dropped"` — it searched the whole corpus and
found that `course_phys_130_exams.txt` contains the same rule, *"the lowest
midterm is dropped"*. So an answer drawn from the wrong course would still
have contained my expected phrase and scored as correct. Claude gave me three
options: keep it, reword the question around `"equally weighted"` (which it
verified appears only in the two STAT 150 files), or replace it. I chose to
replace it with the Kestrel Commons question using `$12.50`, which appears in
exactly one document in the entire corpus. That also gave my five questions a
fifth area of the corpus — dining — that none of the other four touched.

I also used Claude to pressure-test my acceptance criteria after I had written
them. I wrote all five targets and all five justifications myself, including
Criteria 4 and 5, then asked it to tell me how it would test each one using
only the words in the sentence. It did not rewrite them; it identified what
each sentence leaves undefined — for example that Criterion 2's "names at
least one source document" doesn't say whether the CLI's own `Sources
retrieved:` line counts or only the model's text, which matters because the
CLI prints that line either way. I left the wording as written and recorded
the ambiguities instead.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

I ran the baseline with `python run_eval.py --label before`: five questions,
three uncached generations per question, plus one deterministic pass over the
five out-of-scope questions. The complete raw output is in
[`results/run_2026-09-23_1820_before.md`](results/run_2026-09-23_1820_before.md).

The baseline predated `scorer.py`, so its generated report has blank score
cells and preserves the 15 answers for manual judgment. I counted a source for
Criteria 2 and 5 only when the **generated answer itself** named the file; the
CLI's automatic `Sources retrieved:` list did not count. Retrieval, the gate,
and chunking are deterministic, so Criteria 1, 3, and 4 have the same measured
count in all three columns.

## Run Log — Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every generated answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks contain enough context to stand alone | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Named sources actually support the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

### Evidence from the Before Run

**Criterion 1 — answer-bearing chunks.** `store.py::search`, called by
`run_eval.py::run_once`, put the supporting chunk at rank 1 for every question:

| Expected fact | Rank-1 source | Best distance |
|---|---|---:|
| `week two` | `admin_add_drop_deadline.txt` | 0.2547 |
| `40 minutes` | `transit_shuttle.txt` | 0.1799 |
| `10pm` | `study_library_hours.txt` | 0.2192 |
| `$1.25` | `housing_morrow_house_laundry.txt` | 0.1821 |
| `$12.50` | `dining_kestrel_commons.txt` | 0.3643 |

The real retrieval output for the weakest match was:

```text
Question: What does a meal at Kestrel Commons cost without a meal swipe?

#   distance   source
1   0.3643     dining_kestrel_commons.txt

Gate: best distance 0.364 is under the 0.6 cutoff
```

The retrieved chunk, produced by `chunker.py::split_documents`, contains:

```text
Kestrel Commons

Hours are 7:00am to 9:00pm weekdays, 9:00am to 8:00pm weekends.
Costs one meal swipe, or $12.50 cash.
```

**Criterion 2 — source named in the generated answer.** One real baseline
answer from `generate.py::answer_from_chunks` was:

```text
If you drop a course after week two, it shows as a W on your transcript.

Source: admin_add_drop_deadline.txt
```

All 15 generated answers named at least one file in this way.

**Criterion 3 — out-of-scope refusal.** The real output from
`run_eval.py::check_out_of_scope` was:

```text
refused  (best distance 0.825)  What is the capital of Mongolia?
refused  (best distance 0.923)  How do I change the oil in a diesel engine?
refused  (best distance 0.886)  Who won the 1994 World Cup?
refused  (best distance 0.849)  What is the recommended dosage of ibuprofen for a headache?
refused  (best distance 0.864)  How do I write a for loop in Rust?
-> gate refused 5 of 5
```

`gate.py::check` stopped all five before generation.

**Criterion 4 — chunks stand alone.** I reran `app.py::cmd_chunks` with
`python app.py chunks -n 5`. It deterministically printed the same five full
chunks preserved above under **Sample Chunks**:

```text
173 chunks total. Showing 5, spread across the corpus.

Chunk 1 | admin_add_drop_deadline.txt#0
Chunk 2 | course_cs_340_exams.txt#1
Chunk 3 | course_stat_150_exams.txt#0
Chunk 4 | housing_aldridge_hall.txt#0
Chunk 5 | housing_morrow_house.txt#3
```

All five include a title naming the subject and a complete body thought. None
requires the preceding or following chunk, so the result is 5/5.

**Criterion 5 — citation support.** This baseline answer named two sources:

```text
It costs $1.25 to dry a load of laundry in Morrow House.

Sources: housing_morrow_house_laundry.txt and housing_morrow_house.txt
```

The actual text loaded by `ingest.py::load_documents` from the first named file
is:

```text
Laundry in Morrow House

Machines take $1.50 wash, $1.25 dry, coin or card.
```

I made the same comparison for every answer. All 15 answers named a retrieved
file containing the expected fact.

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer | MET | Every expected fact appeared in the rank-1 chunk, so all three runs were 5/5 against a 4/5 target. |
| 2 | Every answer names a source | MET | The generated text—not the CLI footer—named a source in all 15 answers, so every run was 5/5. |
| 3 | Gate stops out-of-corpus questions | MET | `gate.py::check` refused 5/5; their distances (0.825–0.923) were all above 0.6. |
| 4 | Chunks stand alone | MET | All five stride-sampled chunks had a subject-bearing title and one complete thought, for 5/5 against a 4/5 target. |
| 5 | Named sources support the answer | MET | For all 15 answers, at least one filename in the generated answer was retrieved and its document contained the expected fact. |

### Opposite-Verdict Check

Before accepting those verdicts, I tested the strongest reasonable case for
calling each one MISSED:

| Criterion | Strongest case for MISSED | Why the evidence still supports MET |
|---|---|---|
| 1 | The raw report lists retrieved filenames rather than the complete retrieved chunks. | A separate top-5 retrieval audit inspected the actual text and found every expected fact in the rank-1 chunk. |
| 2 | The criterion does not say whether the CLI's automatic `Sources retrieved:` footer counts. | I excluded that footer; all 15 model-generated answers still named a source file. |
| 3 | The out-of-scope table records gate decisions but not the returned refusal sentence. | Exercising the unchanged `run_once` refusal path returned the exact required sentence for all five questions. |
| 4 | "Complete thought" is subjective, and the Morrow sample combines laundry and noise. | Both facts are understandable without a neighboring chunk; even rejecting that sample would leave 4/5, which meets the original target. |
| 5 | A multi-source answer might need every named file, rather than only one, to support it. | The only multi-source answers named the two Morrow files, and both contain the stated `$1.25` drying price. |

## Diagnoses

None of the five criteria missed. Four targets were deliberately 4/5 and the
observed result was 5/5, so those targets were conservative. Criterion 4 is the
least demanding and least reproducible: it inspects only 5 of 173 chunks, and
"complete thought" is not operationally defined. In a future iteration I
would keep the historical criterion and add a stricter version underneath it:
inspect a predetermined stride sample of 20 chunks and require at least 18 to
name their subject, contain complete sentences, and need no neighboring chunk
for interpretation.

### Observed Weakness: Retrieval Precision Below Rank 1

This is not a missed acceptance criterion. It is a measurable efficiency and
risk issue revealed by examining the successful baseline. With `TOP_K = 5`,
the shuttle answer
was followed by four chunks about jobs, dining, library hours, and walking.
The library answer was followed by three dorm-noise chunks and a library-holds
chunk. For the Morrow House laundry question, ranks 3–5 described other dorms
with different prices. Generation ignored these distractors in all 15 runs,
but they added tokens and gave the model conflicting numbers it did not need.

Loading and chunking were not the cause—the answer was intact in every rank-1
chunk. The embedding was also separating the right item. The issue was the
retrieval setting: asking for five results after the useful evidence had
already been found.

## The Improvement

**What I changed:** I changed `config.py::TOP_K` from 5 to 3. I left the
corpus, chunker, embedding model, relevance cutoff, generation prompt, and test
questions unchanged, so the before/after comparison isolates retrieval depth.

I also added `scorer.py::judge` as evaluation instrumentation. It does not run
inside the question-answering pipeline. During `run_eval.py`, it marks a run as
passing only when the answer contains the predeclared expected fact, a
retrieved chunk contains that fact, and the generated answer names that
chunk's source.

**Why I picked it:** Every baseline answer-bearing chunk ranked first, while
ranks 4 and 5 added distractors. Keeping three results preserves fallback
context but removes 40% of the retrieved chunks from every prompt. This
directly addresses the retrieval-precision diagnosis above.

### Controlled Experiment Record

- **Improvement:** reduce retrieval depth from `TOP_K = 5` to `TOP_K = 3`.
- **Problem it targets:** avoidable low precision below the correct rank-1
  result, which added unrelated or conflicting context to generation.
- **System file changed:** `config.py` only.
- **BEFORE behavior:** retrieve five chunks for every question.
- **AFTER behavior:** retrieve three chunks for every question.
- **Held constant:** corpus, five questions, five criteria, chunking, embedding
  model, vector index, cosine distance, relevance cutoff, grounding prompt,
  generation model, and generation behavior.
- **Evaluation-only instrumentation:** `scorer.py` reports repeatable verdicts
  during `run_eval.py`; it is not imported by the user-facing question-answer
  pipeline and does not change retrieval or generation.

### Run Log — After

The authoritative fresh AFTER output is in
[`results/run_2026-09-25_1224_after.md`](results/run_2026-09-25_1224_after.md).
It records `TOP_K = 3`, three uncached runs for each question, every generated
answer, every retrieved source list, and the out-of-scope gate evaluation.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every generated answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks contain enough context to stand alone | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Named sources actually support the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Representative real output from that file is:

```text
Question: What does a meal at Kestrel Commons cost without a meal swipe?
Run: 1
Best distance: 0.3643 (passed the gate)
Sources retrieved: dining_kestrel_commons.txt,
                   dining_kestrel_commons_followup.txt,
                   dining_north_kitchen.txt

A meal at Kestrel Commons costs $12.50 cash without a meal swipe.

Source: dining_kestrel_commons.txt
```

The same run's question-level summary was:

```text
If I drop a course, after which point does it show as a W on my transcript?     pass / pass / pass
How often does the campus shuttle run on weekends?                              pass / pass / pass
What time does the library close during reading week?                           pass / pass / pass
What does it cost to dry a load of laundry in Morrow House?                     pass / pass / pass
What does a meal at Kestrel Commons cost without a meal swipe?                  pass / pass / pass
Out-of-scope gate                                                               refused 5 of 5
```

### Before vs. After

| Criterion | Before | After | Change |
|---|---|---|---|
| 1. Retrieved chunks contain the answer | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | No regression |
| 2. Every generated answer names a source | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | No regression |
| 3. Gate stops out-of-corpus questions | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | No regression |
| 4. Chunks contain enough context to stand alone | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | Unchanged; chunking was held constant |
| 5. Named sources actually support the answer | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | No regression |

| Measurement | Before | After | Change |
|---|---:|---:|---:|
| Retrieved chunks per prompt | 5 | 3 | -2 (-40.0%) |
| Model calls | 15 | 15 | 0 |
| Input tokens | 6,729 | 4,896 | -1,833 (-27.2%) |
| Output tokens | 436 | 441 | +5 (+1.1%) |
| Total tokens | 7,165 | 5,337 | -1,828 (-25.5%) |

**What diagnosed problem was this intended to fix?** The baseline retrieved
the correct evidence at rank 1 but still sent unrelated or conflicting lower
ranks to the model.

**What happened before?** All criteria passed, but every prompt included five
chunks and the 15 calls consumed 7,165 tokens.

**What happened after?** All criteria still passed, while each prompt included
three chunks and the same 15 calls consumed 5,337 tokens.

**Did the target improve?** Yes. Retrieved context fell by 40%, input use fell
by 27.2%, and total use fell by 25.5%. Best distances were unchanged because
the same nearest chunks remained rank 1.

**Did another criterion regress?** No. Every criterion remained 5/5 in every
run, and the gate still refused all five unsupported questions.

**Did the improvement help overall?** Yes. It reduced unnecessary context and
token use without changing the measured answer, citation, gate, or chunk
quality outcomes.

There was one useful evaluation failure on the way. The first automated after
run is preserved in
[`results/run_2026-09-23_1829_after.md`](results/run_2026-09-23_1829_after.md).
Its first answer correctly said "after the end of the second week" and cited
`admin_add_drop_deadline.txt`, but the first scorer required the literal phrase
`week two` and marked it false. That was a scorer defect, not a generation
failure. I changed the scorer generically to treat cardinal/ordinal forms and
word ordering as equivalent, while still requiring both a supporting chunk
and its filename in the answer, then re-ran all 15 generations. The fresh
authoritative run passed all 15. I kept the failed log because it is part of the measurement →
diagnosis → fix → re-measurement trail.

## What's Still Broken

No acceptance criterion is still missed, but the evaluation does not prove the
system is finished:

- Five hand-written questions are a small, familiar test set. I would add
  held-out paraphrases and questions with near-matching but wrong entities to
  test whether the rank-1 result stays correct outside this set.
- `TOP_K = 3` still admits distractors: the shuttle prompt still includes jobs
  and dining, for example. A reranker or hybrid lexical/vector search could
  improve precision, measured with precision@3 or mean reciprocal rank.
- `scorer.py` checks the predeclared fact and a supporting citation, but it
  cannot detect an extra unsupported sentence. Structured citations tied to
  chunk IDs would make that stricter than free-form filenames.
- Criterion 4 inspected 5 of 173 chunks. A full automated boundary check could
  catch an unusual chunk that the stride sample misses, although judging
  whether a thought is complete still needs a person or a stronger rubric.

I stopped after one controlled pipeline change because changing retrieval,
chunking, and prompting together would make the before/after result impossible
to attribute.

## What I'd Do Differently

In a future iteration, I would redesign Criterion 4 while preserving its
original historical wording in `criteria.md`. I would add this stricter,
repeatable version underneath it:

> Using 20 chunks selected by a predetermined stride across the full corpus,
> at least 18 must name their subject, contain complete sentences, and be
> understandable without either neighboring chunk.

The original criterion samples only 5 of 173 chunks and uses the subjective
phrase "one complete thought." The future version increases coverage, fixes
the sample selection in advance, and defines observable qualities more
clearly. I did not alter the Project 1 criterion for this experiment.

## How I Used AI in Unit 2

I used OpenAI Codex to execute the evaluation commands, organize the repeated
results, compare raw evidence with the five original criteria, suggest several
plausible explanations for the observed retrieval pattern, implement the one
selected top-k change, and help structure the before/after write-up. I reviewed
and confirmed the verdicts, selected the retrieval-precision diagnosis, and
chose the single improvement before it was treated as final.

The counts, answers, distances, citations, and token totals above come from
the genuine saved runs and command output rather than invented or estimated
results. I kept the scorer's initial false-negative run in `results/` so the
record includes the failed measurement and why the evaluation rule changed.
