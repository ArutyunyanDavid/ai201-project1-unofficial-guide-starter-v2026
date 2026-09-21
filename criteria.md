# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1 **before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something a person could plainly observe. *"Retrieval works"* is an opinion. *"For at least 4 of my 5 test questions, the top results include a chunk containing the answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a stricter or looser one. A reason that says something about your corpus or your pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that contains the answer.

**Why this target:**
I chose 4 out of 5 because retrieval depends on how closely the wording of a question matches the wording in my document chunks. I expect most questions to retrieve useful information, but allowing one miss accounts for a question whose answer may be phrased differently or split across chunks.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
I chose all five because my pipeline has access to the source information for the chunks it retrieves, so including a source should be possible for every generated answer. If an answer does not name a source, it would be difficult for a user to verify where the information came from.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate stops it and the system returns "I don't have enough information about that" — in at least 4 of 5 tries.

**Why this target:**
I chose 4 out of 5 because the relevance gate depends on similarity scores, and unrelated questions can sometimes still appear somewhat similar to text in the corpus. I want the gate to reject most unsupported questions while allowing for one case where the similarity cutoff does not separate an out-of-scope question perfectly.

---

## 4. Chunks contain enough context to stand on their own

At least 4 out of 5 inspected chunks should contain a complete thought and enough context to understand the information without needing a neighboring chunk.

**Why this target:**
I chose 4 out of 5 because the chunks need enough context for retrieval and answer generation to work reliably. However, because chunk boundaries are created automatically, I think allowing one chunk with an incomplete idea or missing context is realistic.

---

## 5. Source citations actually support the answer

For at least 4 out of 5 test questions, the source document named in the generated answer should actually contain information that supports the answer.

**Why this target:**
I chose 4 out of 5 because naming a source is only useful if that source really supports what the system says. The retrieval and generation steps could occasionally connect an answer to the wrong document, so allowing one citation mistake is realistic while still requiring the system to be correct most of the time.

---
