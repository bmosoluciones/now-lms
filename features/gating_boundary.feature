# Engineer-owned acceptance spec (Wall 1 — hash-pinned; edits require re-init
# of the harness manifest by the engineer). Records the SHIPPED gating boundary
# (000-docs/010-AT-ADEC): courses gated, catalog replaced by the doctrine
# teaser, contact zombie dead. scripts/deploy-smoke.sh hard-fails a deploy that
# violates these scenarios. Fork-local; never offered upstream.
#
# Glue status: exercised today by tests/test_intent_learn_front_door.py and
# scripts/deploy-smoke.sh; pytest-bdd step glue is a candidate follow-up.

Feature: Anonymous gating boundary
  Anonymous visitors never see course names, vendor names, or content; the
  most-primed visitor is routed to the intake instead of a dead end. Members
  are unaffected — their path is the dashboard and native enrollment checks.

  Scenario: The public catalog is a doctrine teaser
    When an anonymous visitor requests GET /course/explore
    Then the response is 200
    And the page is the practice-tracks teaser
    And the page contains no course names and no vendor names

  Scenario: Anonymous hit on a gated course converts instead of dead-ending
    Given a course is gated (publico is false)
    When an anonymous visitor requests the course view page
    Then the response is a 302 redirect to /request-access

  Scenario: Authenticated but unenrolled visitors keep the native 403
    Given a logged-in user who is not enrolled in a gated course
    When the user requests the course view page
    Then the response is 403

  Scenario: The contact zombie stays dead while disabled
    Given enable_contact is disabled in settings
    When any visitor requests GET /contact
    Then the response is 404

  Scenario: Landing CTAs point at the intake
    When an anonymous visitor requests GET /
    Then every "Request access" CTA links to /request-access
    And no CTA is a raw mailto: link

  Scenario: Enrolled members reach their courses
    Given a logged-in user enrolled in a course
    When the user opens the course from their dashboard
    Then the course view renders
