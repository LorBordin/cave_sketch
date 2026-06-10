# Implementation Plan: Persistent 'Clear Session Files' Button [checkpoint: 2deb057]

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "Clear Session Files" button visible and functional in the sidebar on every page of the app, with a toast notification on success.

**Architecture:** Extract the sidebar clear-button logic into a shared `render_sidebar()` function in a new `app/components/sidebar.py` module, then call it from `app.py`, `pages/1_survey_plot.py`, and `pages/2_satellite_map.py`. This avoids duplicating the button logic and keeps all three pages consistent.

**Tech Stack:** Python, Streamlit (`st.sidebar`, `st.button`, `st.toast`, `st.rerun`), `shutil` for temp-dir cleanup.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `app/components/sidebar.py` | `render_sidebar()` — renders the clear button with toast |
| Modify | `app/app.py` | Replace inline button with `render_sidebar()` call |
| Modify | `app/pages/1_survey_plot.py` | Add `render_sidebar()` call |
| Modify | `app/pages/2_satellite_map.py` | Add `render_sidebar()` call |

---

### Task 1: Create the shared sidebar component

**Files:**
- Create: `app/components/sidebar.py`

- [x] **Step 1: Write the file with the `render_sidebar` function** d7fb8db
- [x] **Step 2: Verify the file exists and imports cleanly**
- [x] **Step 3: Commit**

```bash
git add app/components/sidebar.py
git commit -m "feat: add shared sidebar component with clear-session button and toast"
```

---

### Task 2: Update `app.py` to use the shared sidebar

**Files:**
- Modify: `app/app.py`

- [x] **Step 1: Replace the inline sidebar block with `render_sidebar()`** 8573aa6
- [x] **Step 2: Run the app and manually verify the button appears on the main page**
- [x] **Step 3: Commit**

```bash
git add app/app.py
git commit -m "refactor: use shared render_sidebar() in app.py"
```

---

### Task 3: Add sidebar to Survey Plot page

**Files:**
- Modify: `app/pages/1_survey_plot.py`

- [x] **Step 1: Add `render_sidebar()` call after `init_session()`** fb0a445
- [x] **Step 2: Navigate to the Survey Plot page and verify the button**
- [x] **Step 3: Commit**

```bash
git add app/pages/1_survey_plot.py
git commit -m "feat: add persistent clear-session sidebar to Survey Plot page"
```

---

### Task 4: Add sidebar to Satellite Map page

**Files:**
- Modify: `app/pages/2_satellite_map.py`

- [x] **Step 1: Add `render_sidebar()` call after `init_session()`** d7724a7
- [x] **Step 2: Navigate to the Satellite Map page and verify the button**
- [x] **Step 3: Commit**

```bash
git add app/pages/2_satellite_map.py
git commit -m "feat: add persistent clear-session sidebar to Satellite Map page"
```

---

### Task 5: Acceptance criteria walkthrough

- [x] **Step 1: Full end-to-end verification**
- [x] **Step 2: Conductor - User Manual Verification 'Implementation' (Protocol in workflow.md)**
