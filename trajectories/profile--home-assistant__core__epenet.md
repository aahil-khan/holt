# Trajectory — contributor profile — epenet in home-assistant/core

`holt next` ranks open issues for somebody who has already merged work in a repository. This agent turns that person's merged pull requests and the review feedback on them into a competence profile, which feeds exactly one term in the ranking.

It was measured and cut: adding the profile term moved **0 of 88** rankings — 0 wins, 0 losses, 88 ties — which is why the shipped `holt next` runs no model call and costs nothing. The call is here because the experiment is in the changelog and the record should be readable.

Rendered from `fixtures/trajectories/progression/home-assistant__core__epenet.jsonl`, one of 1 recorded call(s) in that file. Replayed from committed recordings; no model ran.

---

## The profile call

*Model:* `gpt-5-mini-2025-08-07` · *645 in / 1085 out tokens · $0.0023*

<details><summary>Instructions given to the model</summary>

```
You are reading one contributor's merged pull requests in a
single repository, together with what reviewers said to them.

Describe what this person has **demonstrably** worked on. Not what they might be
good at, and not a compliment: only what the merged work and the review feedback
actually show.

  * areas: parts of the project they have touched. Use the vocabulary of the
    repository itself -- directory names, subsystem names, feature names.
  * skills: what kind of work they did. "packaging", "test fixtures",
    "documentation", "API endpoints", "build configuration".
  * ready_for: one sentence on the next step up in scope that their history
    supports. Be specific and be conservative; if the history is thin, say so.

If two merged pull requests are all you have, say what those two show and nothing
more.
```
</details>

<details><summary>Evidence it was shown (first 2000 chars)</summary>

```
Repository: home-assistant/core
Contributor: epenet

Their merged pull requests (5 of 5):

--- Refactor Renault to use StrEnum
    10 files, +261/-186
    touched: homeassistant/components/renault/__init__.py, homeassistant/components/renault/config_flow.py, homeassistant/components/renault/const.py, homeassistant/components/renault/diagnostics.py, homeassistant/components/renault/renault_hub.py, homeassistant/components/renault/services.py, tests/components/renault/const.py, tests/components/renault/test_config_flow.py, tests/components/renault/test_init.py, tests/components/renault/test_services.py
    reviewers said: zweckj
--- Fix incorrect use of Platform enum in component tests
    7 files, +46/-36
    touched: tests/components/indevolt/test_number.py, tests/components/indevolt/test_select.py, tests/components/indevolt/test_switch.py, tests/components/pjlink/test_media_player.py, tests/components/unifi_access/test_select.py, tests/components/unifiprotect/test_relay.py, tests/components/unifiprotect/test_siren.py
    reviewers said: thecode
--- Import notify domain in notify tests
    2 files, +30/-32
    touched: tests/components/apprise/test_notify.py, tests/components/signal_messenger/test_notify.py
    reviewers said: jbouwh
--- Fix CI failure due to missing ssdp patching in braviatv
    1 files, +17/-0
    touched: tests/components/braviatv/conftest.py
    reviewers said: joostlek
--- Bump tuya-device-handlers to 0.0.22
    2 files, +2/-2
    touched: homeassistant/components/tuya/manifest.json, requirements_all.txt
    reviewers said: erwindouna; joostlek
```
</details>

**What it answered:**

```json
{
 "areas": [
  "homeassistant/components/renault (integration code: __init__.py, config_flow.py, const.py, renault_hub.py, services.py, diagnostics)",
  "tests/components/renault (unit tests)",
  "tests/components/indevolt, pjlink, unifi_access, unifiprotect (component tests)",
  "tests/components/apprise, tests/components/signal_messenger (notify tests)",
  "tests/components/braviatv (conftest/test fixtures)",
  "homeassistant/components/tuya (manifest) and repository requirements_all.txt"
 ],
 "skills": [
  "integration refactor to use StrEnum (code + consts)",
  "updating config_flow, diagnostics and service code for an integration",
  "editing/updating unit tests across multiple integrations",
  "fixing incorrect enum usage in tests (Platform)",
  "adding/importing domains in tests (notify)",
  "test fixture/conftest adjustments and ssdp patching to resolve CI failures",
  "dependency bumping / manifest and requirements updates"
 ],
 "ready_for": "Can take ownership of a full integration migration to updated types/APIs (e.g., converting an integration to StrEnum) including updating its tests and fixing related CI/test-fixture issues."
}
```

