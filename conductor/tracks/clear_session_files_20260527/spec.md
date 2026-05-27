# Specification: Persistent 'Clear Session Files' Button

## Overview
The application requires a "Clear Session Files" button to be persistently visible and functional across all main sections of the app (e.g., Survey Plot, Satellite Map). This ensures users can easily reset their workspace without navigating back to a specific start page.

## Functional Requirements
- **Location:** The "Clear Session Files" button must be placed in the standard Streamlit sidebar (`st.sidebar`) so it is accessible from any page.
- **Functionality (Hard Reset):** Clicking the button must perform a full reset of the user's session. This involves clearing all relevant `st.session_state` variables and potentially removing any temporary files associated with the session, effectively returning the app to its initial state.
- **Feedback:** Upon successful execution of the clear action, a brief success message (toast notification) should be displayed to the user.

## Technical Context
- The app is a Streamlit multi-page app (`app/app.py` + `app/pages/`). In Streamlit's multi-page architecture, sidebar content defined in one page is **not** automatically visible on other pages. Each page must render its own sidebar content. A shared `render_sidebar()` component function must be created and called from all pages.
- A partial implementation already exists in `app/app.py` (the `🗑️ Clear Session Files` button with `shutil.rmtree` + `st.session_state.clear()` + `st.rerun()`), but it lacks the toast notification and is absent from the two sub-pages.
- After `st.session_state.clear()` + `st.rerun()`, `init_session()` is called again on the rerun, which correctly creates a new `files_dir` UUID and reinitializes all defaults — no extra re-init logic is needed.

## Non-Functional Requirements
- **Consistency:** The button's appearance and behavior must be identical across all pages where the sidebar is rendered.

## Acceptance Criteria
- [ ] A "Clear Session Files" button is visible in the sidebar on the main page, Survey Plot page, and Satellite Map page.
- [ ] Clicking the button clears the current session state completely.
- [ ] After clicking, a success toast message appears confirming the reset.
- [ ] The user can immediately start a new workflow (e.g., upload new files) after clearing.

## Out of Scope
- Granular clearing of specific files or state keys (this is an all-or-nothing reset).