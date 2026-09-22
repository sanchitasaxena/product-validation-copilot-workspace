# Synthetic Registry Approval Feature Brief

This document is synthetic reference data. It is not an approved product requirement.

## Approval policy setup

- Scenario: Create an approved provider rule
  Prerequisites: Organization usage control is enabled and no provider rule exists
  Expected result: Rule saves and appears in the approved artifacts list
  Interface: UI

- Scenario: Update an approved provider version
  Prerequisites: T-401
  Expected result: Updated version is displayed and applies to the next workspace run
  Interface: UI

## Run enforcement

- Scenario: Run a workspace using an unapproved provider
  Prerequisites: T-401 and the workspace configuration references an unapproved provider
  Expected result: Run fails before apply and identifies the blocked provider
  Interface: Permissions

## Edge cases

- Duplicate provider approval rules are rejected.
