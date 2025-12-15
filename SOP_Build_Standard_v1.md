# SOP_Build – Folder & Process Standard (v1)

# SOP_Build – Folder & Process Standard (v1)

**Owner:** S. Rajagopalan  
**Purpose:** This repo holds the *canonical* tools and process for building SOP players  
from PPT → PNG → RAW → READY → story.json → _player.html for SE, Palco, and Specialty.

If you are about to “tinker” or fix a bug, **read this first**.

---

## 1. Repo layout (must stay stable)

```text
SOP_Build/
├─ README.md
├─ SOP_Build_Standard_v1.md      ← this document
├─ config/
├─ src/
│   ├─ powershell/
│   └─ python/
├─ inputs/
│   ├─ ppt_sample/
│   ├─ raw/
│   ├─ ready_base/
│   └─ ready_enh/
├─ outputs/
│   ├─ images/
│   ├─ story/
│   └─ players/
├─ logs/
└─ docs/
