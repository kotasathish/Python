# Chatbot Design Document

**Project:** MyBot (chatbot.py)
**Location:** `c:/Users/kotas/source/Python`
**Author:** GitHub Copilot
**Date:** 2026-01-06

---

## 1. Purpose & Scope ✅
This document describes the design for the current chatbot implementation. It covers goals, architecture, components, data, handling of paraphrases & special intents (time, jokes, compliments, wellbeing), testing strategy, deployment, and next steps.

Goals:
- Eliminate repetitive/echo responses and improve relevance. ✅
- Use lightweight paraphrase/synonym matching to handle rephrased questions. 💡
- Add deterministic handlers for common intents (time, jokes, compliments, wellbeing). 🔧
- Keep the system easy to run and maintain (single-file runnable `chatbot.py`). 🧭

Scope:
- Focused on rule + corpus-based approach (ChatterBot + small custom rules). Not a full NLU pipeline.

---

## 2. High-Level Architecture 🏗️

- **Input**: User text (console)
- **Preprocessing**: normalization (lowercase, contraction expansion, punctuation removal)
- **Fast Rule Handlers** (checked first): time queries, compliments, wellbeing, farewell, jokes followups
- **Model Lookup**: ChatterBot `BestMatch` (read-only) with configured similarity threshold
- **Paraphrase Engine**: WordNet-based synonym substitution to generate alternatives when model confidence is low
- **Fallback**: Friendly default message when no confident response
- **Persistence**: SQLite (`database.sqlite3`) used by ChatterBot for statements and lookup

Diagram (text):

User -> normalize_text() -> [fast handlers] -> model.get_response() -> paraphrase attempts -> fallback

---

## 3. Components & Responsibilities 🔧

- `chatbot.py` (single point of entry): main CLI and orchestration
- **Preprocessing**:
  - `normalize_text(s)` — contraction expansion, punctuation removal
  - `generate_paraphrases(text)` — uses NLTK WordNet synonyms and lemmatizer
- **Model**:
  - ChatterBot `ChatBot('MyBot')` with `SQLStorageAdapter` and `BestMatch` logic adapter
  - `ChatterBotCorpusTrainer` for corpus training
- **Handlers** (checked in `get_best_response` before model):
  - `time` detection (returns current time)
  - `jokes` detection and responses
  - `compliments` (e.g., "nice joke") replies
  - `wellbeing` replies (e.g., "am good" → friendly ack)
  - **Future**: farewell intent mapping
- **Config / CLI**:
  - `--retrain` to delete DB and retrain from corpus
  - thresholds: `primary_threshold`, `secondary_threshold`, `min_statements` in code
- **Fallback**: `default_response` string (friendly prompt)

---

## 4. Data & Training 📚

- Uses ChatterBot English corpus (`chatterbot.corpus.english`).
- DB: `database.sqlite3` (SQL storage adapter)
- Training strategy:
  - If `database.sqlite3` missing or has fewer than `min_statements` rows, run training.
  - Option to force retrain with `--retrain` flag.

Data hygiene:
- Avoid auto-learning at runtime (`read_only=True`) to prevent learning noisy responses.

---

## 5. Intent Mapping and Examples 🎯

- Time query
  - Examples: "what's the time?", "time now", "what is the time now"
  - Response: `The current time is HH:MM:SS`
- Joke requests
  - Examples: "tell me a joke", "can you tell me a joke?", "do you know any jokes?"
  - Response: Joke from corpus or custom handler
- Compliment / acknowledgment
  - Examples: "nice joke", "haha", "thanks"
  - Response: e.g., "Glad you liked it!" or "Want another joke?"
- Wellbeing replies
  - Examples: "I'm good", "am good", "doing well"
  - Response: e.g., "Good to hear!"
- Unknown or low confidence
  - Response: `default_response` (e.g., "Sorry, I don't understand...")

---

## 6. Paraphrase Strategy & Thresholds 💡

- Normalize the input first (lower/strip punctuation/expand contractions).
- Generate paraphrases using single-word WordNet synonyms for tokens.
- Score responses via ChatterBot `response.confidence`.
  - If model returns a confident answer (>= primary threshold) quickly, use it.
  - Else query paraphrases and pick the best confidence >= secondary threshold.
  - Otherwise use `default_response`.
- Tunable thresholds are defined in `get_best_response(primary_threshold, secondary_threshold)`.

Tradeoffs:
- WordNet-based paraphrasing is lightweight and fast but primitive. It helps for simple rewordings but not complex paraphrases.
- Using read-only model prevents runaway noise but reduces online learning.

---

## 7. Testing & Validation ✅

Testing strategy:
- Unit tests:
  - `normalize_text` variations
  - `generate_paraphrases` yields related variants
  - Special-handler recognizers (time, jokes, compliments, wellbeing)
- Integration tests:
  - `get_best_response` on representative utterances (greetings, jokes, time)
  - confirm fallback behavior on unknown inputs
- Conversational tests (scenarios):
  1. Ask: "Tell me a joke" → bot returns a joke (confidence > 0.5)
  2. Reply: "nice joke" → bot replies with acknowledgement
  3. Ask: "What's the time?" → bot returns current time
  4. Say: "am good" → bot acknowledges wellbeing
- Add CI to run tests on commit/push

---

## 8. Deployment & Runbook 🚀

Local usage:
- Create and activate virtualenv
- Install dependencies (example):

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python chatbot.py
# optional: python chatbot.py --retrain
```

Production suggestions:
- Containerize with Docker for reproducible environments
- Expose as an API service if needed (Flask/FastAPI wrapper) to decouple CLI from UI

---

## 9. Observability & Maintenance 📊

- Logging: ensure notable events are logged (training, retrain, errors)
- Monitoring: capture counts of fallbacks and top queries to identify model gaps
- Regular retraining: periodically retrain with curated additional phrases if needed

---

## 10. Security & Privacy 🔒

- Ensure `database.sqlite3` is private and not committed to public repos with user data.
- Use pinned versions for dependencies (in `requirements.txt`) and scan for vulnerabilities.
- Avoid storing or transmitting sensitive user data.

---

## 11. Roadmap & Enhancements ✨

Short-term:
- Add a varied jokes handler (randomized jokes, avoid exact repeats). ✅
- Map farewells to a friendly goodbye reply (do not fallback). ✅
- Add unit tests and CI to run them on push. ✅

Medium-term:
- Replace or augment with a small Transformer-based NLU component for better paraphrase handling.
- Add conversation memory (session-based context) so follow-ups are handled correctly.

Long-term:
- Multi-channel support (web, messenger) + analytics dashboard

---

## 12. Acceptance Criteria & Metrics 📈

- Reduction in fallback rate on standard test set by 80% vs baseline.
- Jokes path returns a joke for 95% of direct joke requests.
- Fallback responses limited to < 5% of common queries.

---

## 13. Files & Changes

- **Updated**: `chatbot.py` (training logic, paraphrase helpers, handlers, thresholds)
- **Added**: `DESIGN.md`
- Suggested: add `requirements.txt` and `tests/` folder for unit/integration tests

---

## 14. Next Steps 📝

1. Review this doc and provide feedback or missing intents you'd like covered.
2. Add unit tests for `normalize_text`, `generate_paraphrases`, and handlers.
3. Add CI (GitHub Actions) to run tests and linting on push.
4. (Optional) Add Dockerfile and container workflow for deployment.

---

If you'd like, I can now:
- Create unit tests and CI config, or
- Add a randomized jokes handler and map farewells to proper replies, or
- Convert this doc to a formatted README/MD for repository front page.

Reply with which you want next and I will implement it. ✨
