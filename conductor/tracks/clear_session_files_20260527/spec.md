# Specification: Persistent 'Clear Session Files' Button

## Overview
The application requires a "Clear Session Files" button to be persistently visible and functional across all main sections of the app (e.g., Survey Plot, Satellite Map). This ensures users can easily reset their workspace without navigating back to a specific start page.

## Functional Requirements
- **Location:** The "Clear Session Files" button must be placed in the standard Streamlit sidebar (`st.sidebar`) so it is accessible from any page.
- **Functionality (Hard Reset):** Clicking the button must perform a full reset of the user's session. This involves clearing all relevant `st.session_state` variables and potentially removing any temporary files associated with the session, effectively returning the app to its initial state.
- **Feedback:** Upon successful execution of the clear action, a brief success message (toast notification) should be displayed to the user.

## Non-Functional Requirements
- **Consistency:** The button's appearance and behavior must be identical across all pages where the sidebar is rendered.

## Acceptance Criteria
- [ ] A "Clear Session Files" button is visible in the sidebar on the main page, Survey Plot page, and Satellite Map page.
- [ ] Clicking the button clears the current session state completely.
- [ ] After clicking, a success toast message appears confirming the reset.
- [ ] The user can immediately start a new workflow (e.g., upload new files) after clearing.

## Out of Scope
- Granular clearing of specific files or state keys (this is an all-or-nothing reset).