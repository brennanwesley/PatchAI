# PatchAI Architecture Build Plan Reference Guide

## Purpose

This document is the working reference guide for improving the PatchAI codebase in a phased, priority-driven way while protecting current production stability for paying subscribers.

The phases below map directly to the architecture review priorities:

- **Phase 1** = Priority 1
- **Phase 2** = Priority 2
- **Phase 3** = Priority 3
- **Phase 4** = Priority 4
- **Phase 5** = Priority 5
- **Phase 6** = Priority 6

This plan is intended to provide structure without becoming rigid. We should stay flexible enough to:

- **Respond to newly discovered issues** without losing the larger roadmap
- **Prioritize production safety** over speed or cleanup vanity work
- **Include high-impact, low-complexity improvements** when they clearly improve reliability, maintainability, or user experience

## Working Principles

- **Protect production first**
- **Avoid unnecessary disruption to paying subscribers**
- **Prefer incremental, reversible changes over large rewrites**
- **Clarify the authoritative architecture before removing legacy code**
- **Treat cleanup as strategic work, not cosmetic work**

## Phase 1 - Stabilize Production Engineering Hygiene

### Step 1 - Restore trustworthy CI coverage

- Fix CI so it runs real backend and frontend checks instead of referencing missing files
- Re-establish reliable quality gates so production changes are not protected by broken automation

### Step 2 - Reduce production debug exposure

- Remove or gate production debug logging across auth, chat payloads, and frontend runtime
- Reduce unnecessary operational noise and remove logging that could expose sensitive runtime details

### Step 3 - Review destructive operational surfaces

- Audit and lock down destructive admin endpoints before additional feature work
- Verify that destructive actions are appropriately restricted, justified, or removed

### Step 4 - Standardize environment behavior

- Standardize frontend backend URL fallbacks so services do not silently point at inconsistent environments
- Make environment behavior predictable across development and production

### Step 5 - Establish one current architecture reference

- Create one authoritative current-state architecture reference that matches the deployed application
- Make it easy to identify which files, flows, and systems are truly active

## Phase 2 - Reduce Architecture Drift

### Step 1 - Finalize the chat architecture direction

- Choose and formalize one chat model permanently: single-chat or multi-chat
- Use that decision as the basis for future simplification and deletion work

### Step 2 - Simplify frontend chat state

- Simplify `useChatStore.js` so it reflects actual product behavior instead of preserving unnecessary legacy compatibility
- Reduce complexity in the most central piece of frontend state management

### Step 3 - Remove mismatched legacy logic

- Remove legacy chat service methods and backend assumptions that no longer belong to the chosen chat model
- Align runtime behavior, interfaces, and expectations across the stack

### Step 4 - Separate active runtime from historical artifacts

- Archive or remove obsolete runtime variants and broken backups from the active backend surface
- Make it immediately clear which files are authoritative and which are historical residue

## Phase 3 - Clean the Repository

### Step 1 - Remove isolated debug and test clutter

- Delete isolated debug and test scripts that are not imported by production code
- Reduce repo noise that makes the project harder to reason about

### Step 2 - Organize operational scripts intentionally

- Move maintenance and admin scripts into a clearly named location with simple usage guidance
- Improve discoverability without mixing support scripts into core application areas

### Step 3 - Remove archived runtime debris

- Remove archived runtime files like broken or date-stamped backend variants from the main code surface
- Keep the repository focused on active, maintained code

### Step 4 - Standardize the testing surface

- Keep one clear active testing strategy per layer instead of many ad hoc diagnostic files
- Make the testing story easier to trust and easier to maintain

## Phase 4 - Strengthen Operational Safety

### Step 1 - Audit billing truth sources

- Review Stripe and subscription sync flows end-to-end and document the true source of record for subscription state
- Reduce ambiguity in one of the most business-critical parts of the application

### Step 2 - Clarify operational boundaries

- Consolidate monitoring and Phase 3 operational services behind a clearer boundary
- Make support, troubleshooting, and future maintenance easier

### Step 3 - Create lightweight incident runbooks

- Add a lightweight production runbook for auth failures, Stripe sync failures, chat failures, and Supabase outages
- Improve operational response speed without adding unnecessary process overhead

### Step 4 - Treat database security changes cautiously

- Review RLS posture carefully before any schema or security changes because service-role workflows are deeply embedded
- Avoid breaking production behavior through well-intentioned but unsafe policy changes

## Phase 5 - Improve Maintainability of the Product Core

### Step 1 - Thin down backend app assembly

- Refactor `backend/main.py` so it becomes a thinner application assembly layer instead of carrying too much operational and historical weight
- Improve readability and lower change risk in the main backend entry point

### Step 2 - Normalize backend service patterns

- Normalize backend service interfaces so chat, payment, referral, and monitoring follow more consistent patterns
- Make the codebase easier to extend and safer to modify

### Step 3 - Standardize frontend API access

- Replace mixed direct `fetch` usage and custom wrappers with one consistent frontend API access pattern
- Reduce duplication and inconsistent request behavior across the frontend

### Step 4 - Reduce frontend state complexity

- Cut down reducer complexity and dev-only instrumentation in frontend state management
- Improve maintainability without changing the core user experience

## Phase 6 - Improve the Oilfield Consultant Product Core

### Step 1 - Version consultant behavior intentionally

- Externalize and version the system prompt so PatchAI behavior can evolve safely and deliberately
- Make domain behavior changes easier to review and control

### Step 2 - Add domain-specific evaluation coverage

- Add domain-specific evaluation tests for oilfield consulting quality, not only API or infrastructure behavior
- Measure product quality in terms that matter to the actual customer experience

### Step 3 - Strengthen knowledge grounding

- Define more structured knowledge sources for oilfield guidance instead of relying only on prompt instructions
- Improve consistency, trust, and future extensibility of consultant responses

### Step 4 - Add response quality guardrails

- Add guardrails around uncertainty, operational safety, and clear communication of assumptions
- Improve reliability and reduce the risk of overconfident low-quality answers

## How To Use This Guide

- **Use the phases as the default order of execution**
- **Treat the steps within each phase as the main accomplishment targets**
- **Stay flexible when urgent production issues or clear quick wins appear**
- **Prefer work that reduces risk, clarifies architecture, or simplifies future development**
- **Reassess priorities after each phase rather than assuming the plan must remain static**

## Default Execution Order

- **Phase 1** - Stabilize production engineering hygiene
- **Phase 2** - Reduce architecture drift
- **Phase 3** - Clean the repository
- **Phase 4** - Strengthen operational safety
- **Phase 5** - Improve maintainability of the product core
- **Phase 6** - Improve the oilfield consultant product core

## Outcome Goal

The goal of this build plan is to move PatchAI toward a cleaner, safer, easier-to-maintain architecture without risking current production behavior or losing the flexibility to address newly discovered issues and opportunistic high-value improvements.
