# Engineering-Authored QA Scenario Style Guide

Use the original RAUC bug tracker as the canonical style corpus. Those scenarios were written by the engineering team and represent the style future generated trackers should follow.

This guide is intentionally not a generic usability-testing guide. It documents the engineering-authored bug bash pattern: concise, functional, system-behavior coverage with practical setup dependencies.

## Source corpus

Primary source: original RAUC bug tracker, especially the `Scenarios` tab.

Canonical columns:

- ID
- Feature
- Scenario Description
- Prerequisites
- Expected Result
- Testers
- Status

Canonical feature areas observed in the source corpus:

- Registry usage control
- Registry environment tags
- Assigning tags
- Visibility of tags and environments

These feature areas are functional groupings, not personas.

## Scenario descriptions

Use concise functional wording:

- Create a Registry Environment Tag
- Delete a value and add a new one
- Assign a tag to a Private Registry Module
- Check if Registry Environment Tag-value is visible on the List Module Page
- Using Terraform CLI to create a failing run
- Configuring Correct Tags
- Create a Registry Environment Tag when One already exists
- Add values to the Registry Environment Tag
- Assign a Registry Environment Tag to a Project
- Go to Manage Tags UI and ensure project/workspace counts are accurate

Avoid generic UX/research phrasing:

- Verify that the user can successfully...
- As a user, I want...
- Navigate to this page and click...
- You are a platform engineer trying to...
- How would you feel about...

## Description pattern

Prefer action-object or check-object-result phrasing:

- `Create` + object
- `Assign` + object + target
- `Unassign` + object + target
- `Delete` + object/state
- `Check if` + state + surface
- `List` + object + behavior
- `Using Terraform CLI to` + outcome
- `Configuring` + correct/incorrect state

Keep the description short. The scenario description is not the full test script.

## Prerequisites

Use practical setup language:

- T-110
- T-115/T-120
- A Registry Environment Tag should exist for the org
- Create a couple of Project tags
- Environment Tag exists for the org
- Registry tag with 10 values exists in the org
- The environment tag is assigned to a registry module version
- Create a couple of Project tags, assign same tags to multiple projects

## Dependency style

Dependencies may appear in prerequisite text as scenario IDs:

- `T-110`
- `T-115/T-120`
- `T-122/T-127`

The improved generator should also store dependencies structurally in a `Depends On` field so summaries and validation can detect blocked paths.

## Expected results

Expected results should be observable pass conditions:

- A maximum of 10 values are allowed
- Cannot switch the toggle on for Registry Tag
- The Tag value should appear on the list module page against the private module version
- Upon save the tag should reflect the new value
- Upon save the tag should be deleted from the registry module version it was assigned to
- Performing a run in the Workspace Under Test should fail due to unapproved artifacts
- Performing a run in the Workspace Under Test using the UI should complete without error

Expected results can use bullets when multiple conditions must pass. They should describe observable behavior, not user sentiment or research interpretation.

## Status style

Use operational test statuses:

- Pending
- In Progress
- Passed
- Failed
- Blocked

The original tracker used visual status labels such as `✅ Passed`, `❌ Failed`, `🟡 In Progress`, and `⚪ Pending`. The generator may display icons in Excel, but structured data should store the normalized status.

## Tester assignment style

Support single and multi-tester assignments:

- `Tester A`
- `Tester A, Tester B, Tester C`
- `Tester A (cannot test due to T-115)`

Tester notes inside tester cells are messy but meaningful. The improved tracker should preserve them and optionally parse blockers into a separate notes field.

## Issue row style

Bug tracker rows should preserve practical bug bash language:

- `T-115: Error toast notification is not disappearing, even after navigating away from overview`
- `T-109 : Deleting an environment tag value does not remove it from the assigned module version`
- `T-202: UI - Super Select is jumping on adding new values`
- `No scenario. Noticed a 404 while rendering a public registry module`

Issue types:

- Bug
- Friction
- Improvement

Evidence links may point to Slack, Box, screenshots, logs, or other team systems.

## QA scenarios vs research tasks

QA scenario:

```text
Assign a tag to a Private Registry Module
```

Research task:

```text
You are responsible for making sure only approved modules are used in production. Show me how you would set that up.
```

The QA tracker should use the first style. It validates product behavior. It does not observe participant mental models.

## Inferred scenarios

When documentation does not explicitly support a scenario, mark it as inferred and require engineering review.

Use the same engineering-authored wording even for inferred scenarios, but add `Source Status = inferred` and include the source assumption.

## Generator style checks

Generated scenarios should pass these checks:

- Description is concise and functional.
- Description does not start with `Verify that`, `As a user`, or similar research/story phrasing.
- Feature area is a concrete product/system area.
- Prerequisites describe state or dependency IDs.
- Expected result is observable.
- Inferred scenarios are marked for engineering review.
- Dependencies reference existing scenario IDs.
- Failed scenarios can link to one or more bug rows.
