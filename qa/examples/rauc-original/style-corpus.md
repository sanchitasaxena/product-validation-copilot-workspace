# RAUC Original Tracker Style Corpus

This file captures representative patterns from the original RAUC bug tracker. Use it to guide future QA scenario generation and validation.

## Feature areas

- Registry usage control
- Registry environment tags
- Assigning tags
- Visibility of tags and environments

## Scenario descriptions

- Reserved key creation attempt when one already exists
- Toggle 'Hide' on 'Prod' tags
- Create a Registry Environment Tag
- Create a Registry Environment Tag when One already exists
- Add values to the Registry Environment Tag
- Add as many values as the UI allows you to
- Delete a value and add a new one
- Delete a value that has been assigned to a Registry Module Version
- Assign a tag to a Private Registry Module
- Unassign a tag from a Private Registry Module
- Check if Registry Environment Tag-value is visible on the List Module Page
- Go to Manage Tags UI and ensure project/workspace counts are accurate
- Assign a Registry Environment Tag to a Project
- Setup a workspace for usage control
- Using Terraform CLI to create a failing run
- Configuring Correct Tags
- Configuring Incorrect Tags

## Prerequisite patterns

- `T-110`
- `T-115`
- `T-125/T-120`
- `A Registry Environment Tag should exist for the org`
- `Create a couple of Project tags`
- `Environment Tag exists for the org`
- `Registry tag with 10 values exists in the org`

## Expected result patterns

- `All tags save and display`
- `Tags disappear from UI`
- `Can save the tag after adding values`
- `A maximum of 10 values are allowed`
- `Cannot switch the toggle on for Registry Tag`
- `The Tag value should appear on the list module page against the private module version`
- `Performing a run in the Workspace Under Test should fail due to unapproved artifacts`

## Bug row patterns

- `T-115: Error toast notification is not disappearing, even after navigating away from overview`
- `T-109 : Deleting an environment tag value does not remove it from the assigned module version`
- `T-110: Effective tag bindings API does not return newly added project tags`
- `T-202: UI - Super Select is jumping on adding new values`
- `No scenario. Noticed a 404 while rendering a public registry module`

## Style summary

The engineering-authored style is terse and functional. It prioritizes coverage and test execution over polished prose. Future generated trackers should match this style while adding structure, validation, and summaries around it.

