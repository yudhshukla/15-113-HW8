### **Acceptance Criteria Reviews:**

1. [PASS] **User introduction and quiz testing** — main.py displays welcome message and main.py allows users to take quiz without login first.

2. [PASS] **Login/Register system** — main.py implements robust PBKDF2 password hashing with salt (main.py), user registration validates duplicates, and login validates credentials correctly. Passwords use `getpass` module for secure input.

3. [PASS] **Performance information access** — main.py provides `view_performance()` function and main.py displays performance stats after quiz with total attempts, correct answers, and proficiency by difficulty.

4. [PASS] **Secure non-human-readable performance files** — performance.py uses pickle for binary serialization (not human-readable), and both performance.store and users.json are chmod'd to `0o600` (main.py and performance.py).

5. [PASS] **Difficulty filtering** — main.py allows users to filter by difficulty. performance.py correctly weights proficiency by difficulty (Easy=1, Medium=2, Hard=3), fulfilling the requirement to "consider difficulty."

6. [FAIL] **Feedback influence on question selection** — The spec states feedback should "influence what kinds of questions they see." Code collects feedback (main.py) and stores it (main.py), but main.py passes empty `user_prefs={}` to `select_questions()`. The stored feedback is never read or used to influence future question selection. **Feature not implemented.**

7. [FAIL] **Missing feature: Question editing** — Spec requires "ability for users to modify questions in a human-readable json file." There is no menu option, function, or interface for users to edit questions. Questions can only be manually edited outside the app. **Feature not implemented.**

---

### **Error Handling & Robustness:**

8. [FAIL] **Crash on missing question 'id' field** — main.py uses `q['id']` with bracket notation in direct access. If a question lacks an `'id'` field, this causes `KeyError`. Should use `q.get('id')` for safety. **Crash vector: add question to questions.json without 'id' field.**

9. [PASS] **Missing questions.json** — main.py handles gracefully with error message and returns empty list.

10. [PASS] **Corrupted/invalid JSON** — main.py catches `JSONDecodeError` and reports clearly.

11. [PASS] **Corrupted performance.store** — performance.py catches exceptions and returns empty structure.

12. [PASS] **Invalid user input** — main.py loops until valid integer for quiz count; main.py validates answer input with retries.

---

### **Code Quality Issues:**

13. [WARN] **Repeated code: Difficulty filtering** — Difficulty filter logic appears in two places: main.py and main.py. Violates DRY principle. Refactor into single helper function.

14. [WARN] **Unused parameter: user_prefs** — main.py accepts `user_prefs` parameter but always called with empty dict (main.py). Dead code path; removes future maintainability for feedback feature.

15. [WARN] **Random.choices weighting fallback logic unclear** — main.py complex handling of duplicates and fallback to `random.sample()` loses the weighting. If weighting fails, it degrades gracefully, but this silent degradation should be documented or logged.

---

### **Security:**

16. [WARN] **chmod() failures silently ignored** — main.py and performance.py use try/except with `pass` for file permission errors. If chmod fails (e.g., file system doesn't support), files remain unprotected without user notification. Consider warning message or skip on unsupported systems (e.g., Windows).

17. [PASS] **Password hashing** — Uses PBKDF2-HMAC-SHA256 with 100,000 iterations and salt storage (main.py), which is cryptographically sound.

---

### **UX Issues:**

18. [WARN] **No feedback on question edit failure** — If a question is missing 'difficulty' field, it silently becomes 'Unknown' (performance.py). User stats then include this unlabeled category. Record should validate or warn.

19. [WARN] **Confusing menu options** — main.py accepts both numbers (1/2/3) and words (start/view/quit). Prompt says "Select an option (1/2/3)" but also accepts 's', 'v', 'q' without documenting this. Reduces clarity.

---

### **Missing Implementation Summary:**

| Feature | Status | Notes |
|---------|--------|-------|
| User introduction | ✓ | Clear welcome message |
| Login/register | ✓ | Robust with PBKDF2 |
| Performance tracking | ✓ | Binary, secure, weighted by difficulty |
| Difficulty filtering | ✓ | Works, case-insensitive |
| **Feedback influences selection** | ✗ | Collected but never used |
| **Question editing interface** | ✗ | No app feature for this |

---

### **Summary:**
The implementation is **mostly complete** with **2 critical missing features** (feedback-driven selection, question editing), **1 crash vector** (missing 'id' field), and several **code quality/UX concerns**. Core functionality (quiz, login, performance tracking, difficulty filtering) works as specified.