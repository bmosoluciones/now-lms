# Engineer-owned acceptance spec (Wall 1 — hash-pinned; edits require re-init
# of the harness manifest by the engineer). Records the SHIPPED behavior of the
# /request-access intake (000-docs/009-AT-ADEC, 000-docs/011-PP-PLAN — copy is
# founder-locked). Fork-local; never offered upstream.
#
# Glue status: scenarios are exercised today by tests/test_request_access.py
# (pytest) and scripts/deploy-smoke.sh (production smoke); pytest-bdd step glue
# is a candidate follow-up, not a gate.

Feature: Request access intake
  The waiting list is the only public conversion path. Submissions store
  durably in the native contact_messages table with an "[ACCESS] " subject
  discriminator; Slack notification is best-effort and never breaks a
  submission.

  Background:
    Given the platform is deployed with the intent_learn theme
    And the request_access blueprint is registered

  Scenario: Anonymous visitor sees the intake form
    When an anonymous visitor requests GET /request-access
    Then the response is 200
    And the page renders the intake form
    And the page offers the secondary "prefer email?" mailto path

  Scenario: A valid submission stores a ContactMessage and confirms
    Given a visitor fills name, email, work links, and what they are building
    When the visitor submits the form with a valid CSRF token
    Then a contact_messages row is stored with subject prefix "[ACCESS] "
    And the vetting fields are composed into the message as a labeled template
    And the visitor is redirected to the post-submit confirmation
    And a best-effort Slack ping is attempted after the database commit

  Scenario: Slack being down never loses a submission
    Given the Slack webhook is unreachable
    When a visitor submits a valid request
    Then the contact_messages row is still stored
    And the visitor still reaches the confirmation page

  Scenario: Honeypot submissions pretend success and store nothing
    Given a bot fills the honeypot field
    When the form is submitted
    Then the response redirects to the confirmation page
    And no contact_messages row is stored

  Scenario: Submissions without a valid CSRF token are rejected
    When a POST to /request-access omits a valid CSRF token
    Then the submission is rejected
    And no contact_messages row is stored

  Scenario: Oversized field values are capped before insert
    Given a visitor submits a name longer than the subject column allows
    When the submission is stored
    Then the "[ACCESS] " subject is truncated to fit String(200)
    And every field is length-capped server-side
