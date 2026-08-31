# Trajectory — Path Finder on NixOS/nixpkgs

Path Finder ranks a repository's open issues by how likely an outsider is to land a fix. It is in the repository, behind a flag, printing its own losing number: precision@3 **0.173** against GitHub's own `good first issue` label at **0.187**, over 3,613 issues. It was cut on a condition written before the feature existed, and it ships anyway because the ranking is still readable evidence and the comparison is the point.

Rendered from `fixtures/trajectories/pathfinder/NixOS__nixpkgs.jsonl`, one of 1 recorded call(s) in that file. Replayed from committed recordings; no model ran.

---

## The Path Finder call

*Model:* `gpt-5-mini-2025-08-07` · *10785 in / 2511 out tokens · $0.0077*

<details><summary>Instructions given to the model</summary>

```
You are helping an outside developer -- someone with no
prior connection to a project -- choose which open issue to attempt first.

You are given issues that were open at a fixed point in time, and evidence about
how the project treated outside contributions before that point.

Rank the issues by one thing only: **how likely is it that an outsider, starting
from nothing, lands a merged pull request resolving this issue?**

That is not the same as "which issue is most important", and it is not the same
as "which issue is easiest". Weigh:

  * whether the issue states a concrete, bounded outcome rather than a wish
  * whether someone could act on it without private context or a design decision
    only a maintainer can make
  * whether the report contains enough to reproduce or locate the problem
  * whether the project's history suggests work of this shape gets merged

An issue labelled for beginners is not automatically a good entry point; many
are aspirational one-liners nobody has scoped. Judge the text, not the label.

Return at most five, best first. For each, say in one sentence what the person
would actually do, and cite the issue's evidence id.
```
</details>

<details><summary>Evidence it was shown (first 2000 chars)</summary>

```
Repository: NixOS/nixpkgs

How this project treated outsiders before the cutoff:
  outsider_merged: 15
  outsider_threads: 100
  median_first_response_hours: 0.8

Issues open at the cutoff (40 of 198 shown):

--- evidence id: issue:NixOS/nixpkgs#526161:opened
    opened 2026-05-30 by mweinelt; 35 comments; labels: ['0.kind: bug', '1.severity: security', '3.skill: sprintable', '3.skill: good-first-bug', '6.topic: old-versions', '5.scope: tracking']
    title: Tracking: Migrate from fuse (2.x) to fuse3 (3.x)
    ### Quick facts - We are [removing](https://github.com/NixOS/nixpkgs/pull/521536) the `fuse` attribute (v2.9.9 from Jan 2019), during the 26.11 release cycle, because it is unsupported upstream. - Migrate packages to `fuse3` instead, which is the maintained continuation of the userspace fuse library. - If your package does not support fuse 3.x - a) file an upstream issue with the project or - b) remove the package if it is unmaintained upstream. - Link back to this issue to allow progress tracking. ### Action items - [ ] adbfs-rootless @Aleksanaa - [ ] hpe-ltfs @redvers - [x] plakar @heph2 @qbit https://github.com/NixOS/nixpkgs/pull/542244 - [ ] python3Packages.fuse-python https://github.com
--- evidence id: issue:NixOS/nixpkgs#523332:opened
    opened 2026-05-23 by LucasOe; 21 comments; labels: ['0.kind: bug', '6.topic: nixos']
    title: nixos/services.displayManager.gdm: GDM shows black screen after updating to 50.0
    ### Nixpkgs version - Unstable (26.05) ### Describe the bug After updating to Gnome/GDM 50.0, I see a black screen, showing only a static underscore, when using GDM with `services.displayManager.gdm.enable = true;`. ### Steps to reproduce 1. Update to nixos-unstable f83fc3c307e74bc5fd5adb7eb6b8b13ffd2a36e1 2. Set `services.displayManager.gdm.enable = true;` and `services.displayManager.defaultSession = "niri";` Note that I'm not using the Gnome Desktop Environment, only GDM. The full steps to reproduce this issue are hard to debug for me wit
```
</details>

**What it answered:**

```json
{
 "ranked": [
  {
   "evidence_id": "issue:NixOS/nixpkgs#525926",
   "first_step": "Open a PR cherry\u2011picking the upstream curl commit that fixes the busy\u2011loop bug (commit 2a2104f3...) into nixpkgs' curl package, add a short test or justification and link the upstream curl issue and this ticket.",
   "why": "The issue names an upstream commit that reportedly fixes the problem and requests it to be cherry\u2011picked into nixpkgs, so a small, well\u2011scoped patch to the curl derivation is reproducible and likely to be accepted (see issue:NixOS/nixpkgs#525926)."
  },
  {
   "evidence_id": "issue:NixOS/nixpkgs#526193",
   "first_step": "Create a small PR to preserve TZDIR in the Hyprland wrapper (or add TZDIR to the wrapper environment/preserved variables) so flatpaks and other apps can find zoneinfo; reference the wrapper code and the linked unsecvars.h.",
   "why": "This is a narrowly scoped wrapper/env problem with clear cause \u2014 the wrapper drops TZDIR \u2014 and the fix is a targeted change to the wrapper environment, so an outsider can implement and test a small patch (see issue:NixOS/nixpkgs#526193)."
  },
  {
   "evidence_id": "issue:NixOS/nixpkgs#525573",
   "first_step": "Submit a PR to the stevenblack generator in nixpkgs to filter out link\u2011local entries with a zone index (addresses containing '%') or specifically omit fe80::1%lo0 when producing hosts for dnsmasq, with a test reproducing the failure.",
   "why": "This bug is concrete and easily reproducible (dnsmasq crashes on an entry with a '%' zone index); changing the generator to omit such lines is a small, bounded packaging/module change likely to be accepted (see issue:NixOS/nixpkgs#525573)."
  },
  {
   "evidence_id": "issue:NixOS/nixpkgs#526285",
   "first_step": "Open a docs PR add
```

