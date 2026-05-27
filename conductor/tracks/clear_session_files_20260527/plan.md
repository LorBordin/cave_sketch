# Implementation Plan: Persistent 'Clear Session Files' Button

## Phase 1: Implementation
- [ ] Task: Write failing UI test or define manual test criteria for button visibility and functionality.
- [ ] Task: Locate the central sidebar rendering logic (or update individual pages if a central component isn't used).
- [ ] Task: Add the "Clear Session Files" button to the sidebar.
- [ ] Task: Implement the callback/logic to perform a hard reset (clear `st.session_state` and related files).
- [ ] Task: Add the success toast notification (`st.toast`) upon successful reset.
- [ ] Task: Verify button appearance and functionality across all main pages (Main, Survey Plot, Satellite Map).
- [ ] Task: Conductor - User Manual Verification 'Implementation' (Protocol in workflow.md)