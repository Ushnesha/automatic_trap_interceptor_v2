# SmartBin Deployment Documentation Index

Complete deployment guide for real-world SmartBin on Raspberry Pi 5 with ArduCAM TOF camera, L298N motor driver, and Mecanum wheels.

---

## 📚 All Documents (in reading order)

### 1. **DEPLOYMENT_QUICK_CARD.md** ⭐ START HERE
- **Purpose:** Quick reference, phases, timeline
- **Read Time:** 10 minutes
- **Contains:** 8-phase deployment, commands, quick fixes
- **Best For:** Getting started quickly, having a checklist

### 2. **WIRING_REFERENCE.md** 
- **Purpose:** Hardware connections and GPIO pinout
- **Read Time:** 15 minutes
- **Contains:** Complete wiring diagram, GPIO layout, power specs
- **Best For:** Before assembly, debugging connection issues

### 3. **DEPLOYMENT_GUIDE_FULL.md** 
- **Purpose:** Comprehensive deployment guide
- **Read Time:** 30 minutes (reference)
- **Contains:** 12 parts covering hardware through optimization
- **Best For:** Detailed step-by-step, troubleshooting deep dives

### 4. **SETUP_CHECKLIST.md**
- **Purpose:** Interactive step-by-step verification
- **Read Time:** 20 minutes (hands-on)
- **Contains:** Hardware tests, software tests, tuning steps
- **Best For:** Verifying each phase is correct

### 5. **CSI_SETUP.md**
- **Purpose:** Camera-specific setup and troubleshooting
- **Read Time:** 15 minutes
- **Contains:** CSI hardware, software, diagnostic tests
- **Best For:** Camera issues, tuning, performance

### 6. **CSI_QUICK_START.md**
- **Purpose:** 5-step camera quick setup
- **Read Time:** 5 minutes
- **Contains:** Enable → Install → Diagnose → Tune → Run
- **Best For:** Just the camera part

### 7. **TOF_MIGRATION.md**
- **Purpose:** Understanding TOF depth detection
- **Read Time:** 10 minutes
- **Contains:** Old HSV vs new TOF, detection methods
- **Best For:** Understanding the detection approach

### 8. **TOF_CSI_CHANGES.md**
- **Purpose:** Complete changelog of code modifications
- **Read Time:** 10 minutes
- **Contains:** What changed, new tools, tuning params
- **Best For:** Understanding code changes

---

## 🚀 Quick Start Path (for impatient deployers)

1. Read: **DEPLOYMENT_QUICK_CARD.md** (10 min)
2. Physical assembly per **WIRING_REFERENCE.md** (1 hour)
3. Follow phases 1-8 in DEPLOYMENT_QUICK_CARD.md (2-3 hours)
4. Use SETUP_CHECKLIST.md to verify each phase (20 min)
5. Troubleshoot using DEPLOYMENT_GUIDE_FULL.md if needed

**Total time:** 3-4 hours from zero to working robot

---

## 🔍 Documentation by Topic

### Hardware Assembly
- WIRING_REFERENCE.md — GPIO pinout, connections, power
- DEPLOYMENT_GUIDE_FULL.md Part 1 — Physical assembly details

### Operating System & Network
- DEPLOYMENT_GUIDE_FULL.md Part 2 — OS installation
- DEPLOYMENT_QUICK_CARD.md Phase 1-2 — Quick OS setup

### Software Installation
- DEPLOYMENT_GUIDE_FULL.md Part 3 — Dependency installation
- DEPLOYMENT_QUICK_CARD.md Phase 3 — Quick install
- CSI_SETUP.md — Camera-specific software

### Hardware Verification
- DEPLOYMENT_GUIDE_FULL.md Part 4 — GPIO, camera, motor testing
- SETUP_CHECKLIST.md Part 2 — Software verification tests
- CSI_SETUP.md "Testing" — Camera diagnostics

### Configuration & Tuning
- DEPLOYMENT_GUIDE_FULL.md Part 5 — Motor wiring, camera depth
- DEPLOYMENT_QUICK_CARD.md Phase 6 — Quick tuning
- CSI_SETUP.md "Tuning" — Depth parameter adjustment
- SETUP_CHECKLIST.md Part 3 — Configuration testing

### Running SmartBin
- DEPLOYMENT_GUIDE_FULL.md Part 6 — Test run, data collection
- DEPLOYMENT_QUICK_CARD.md Phase 7 — First test
- SETUP_CHECKLIST.md Part 4 — Integration testing

### Production Deployment
- DEPLOYMENT_GUIDE_FULL.md Part 7 — Auto-start, logging
- DEPLOYMENT_QUICK_CARD.md Phase 8 — Service setup

### Monitoring & Maintenance
- DEPLOYMENT_GUIDE_FULL.md Part 10 — Health checks, debugging
- DEPLOYMENT_QUICK_CARD.md — Quick commands, metrics

### Troubleshooting
- DEPLOYMENT_GUIDE_FULL.md Part 9 — Problem-by-problem solutions
- DEPLOYMENT_QUICK_CARD.md — Quick fixes table
- CSI_SETUP.md "Troubleshooting" — Camera-specific issues

### Optimization
- DEPLOYMENT_GUIDE_FULL.md Part 11 — Speed, accuracy, power
- DEPLOYMENT_QUICK_CARD.md — Performance targets

### Advanced Features
- DEPLOYMENT_GUIDE_FULL.md Part 12 — Web dashboard, data logging

---

## 📋 Topic-Based Selection Guide

**"I just assembled hardware, how do I start?"**
→ DEPLOYMENT_QUICK_CARD.md Phase 1

**"My camera isn't working"**
→ CSI_SETUP.md Troubleshooting section

**"I need to know all GPIO connections"**
→ WIRING_REFERENCE.md

**"How do I make it auto-start on boot?"**
→ DEPLOYMENT_GUIDE_FULL.md Part 7 or DEPLOYMENT_QUICK_CARD.md Phase 8

**"Motors are jerky, how to fix?"**
→ DEPLOYMENT_GUIDE_FULL.md Part 9 "Motors erratic/jerky"

**"I want to understand the TOF camera system"**
→ TOF_MIGRATION.md + CSI_SETUP.md

**"I need to tune detection parameters"**
→ DEPLOYMENT_QUICK_CARD.md Phase 6 or CSI_SETUP.md "Tuning"

**"How do I monitor performance?"**
→ DEPLOYMENT_GUIDE_FULL.md Part 10 "Monitoring Script"

**"I'm stuck, where do I find the answer?"**
→ DEPLOYMENT_GUIDE_FULL.md Part 9 "Troubleshooting" (very comprehensive)

---

## ⏱ Total Time Breakdown

| Phase | Document | Duration |
|-------|-----------|----------|
| Planning | Read this file + QUICK_CARD | 15 min |
| Assembly | WIRING_REFERENCE + hardware | 1-2 hours |
| OS Setup | DEPLOYMENT_QUICK_CARD Phase 1-2 | 40 min |
| Software | DEPLOYMENT_QUICK_CARD Phase 3-4 | 15 min |
| Verification | SETUP_CHECKLIST + Phase 5 | 15 min |
| Tuning | DEPLOYMENT_QUICK_CARD Phase 6 | 20 min |
| First Test | DEPLOYMENT_QUICK_CARD Phase 7 | 10 min |
| Production | DEPLOYMENT_QUICK_CARD Phase 8 | 5 min |
| **Total** | | **~2.5-4 hours** |

---

## 🎯 Success Milestones

Track your progress through these milestones:

- [ ] **Hardware assembled** → Check against WIRING_REFERENCE.md
- [ ] **Pi boots** → SSH access working
- [ ] **Camera detected** → `libcamera-hello` shows preview
- [ ] **GPIO working** → All pins respond to commands
- [ ] **Motors spin** → Both directions, controlled by Pi
- [ ] **Diagnostics pass** → `tools/diagnose_camera.py` all green
- [ ] **Detection tuned** → `tools/tune_tof.py` shows object
- [ ] **First test passes** → `python3 main_pi.py` detects & moves
- [ ] **Service enabled** → Auto-starts on boot
- [ ] **Production ready** → Catches working in real tests

---

## 🔗 Quick Links to Key Sections

| Need | Document | Section |
|------|----------|---------|
| GPIO pinout | WIRING_REFERENCE.md | Quick GPIO Pinout |
| Power requirements | WIRING_REFERENCE.md | Voltage Levels |
| Motor wiring | WIRING_REFERENCE.md | Motor Connections |
| OS installation | DEPLOYMENT_GUIDE_FULL.md | Part 2 |
| Camera setup | CSI_SETUP.md | Software Setup |
| Motor testing | DEPLOYMENT_QUICK_CARD.md | Quick Test Commands |
| Troubleshooting | DEPLOYMENT_GUIDE_FULL.md | Part 9 |
| Auto-start | DEPLOYMENT_QUICK_CARD.md | Phase 8 |
| Monitoring | DEPLOYMENT_GUIDE_FULL.md | Part 10 |

---

## 🆘 Emergency Reference

**Robot won't start:**
→ DEPLOYMENT_GUIDE_FULL.md Part 9 "Can't SSH into Pi"

**Camera shows error:**
→ CSI_SETUP.md Troubleshooting section

**Motors don't move:**
→ DEPLOYMENT_GUIDE_FULL.md Part 9 "Motors don't move"

**Slow/jerky performance:**
→ DEPLOYMENT_GUIDE_FULL.md Part 9 "Slow performance"

**Can't find what I need:**
→ Search in DEPLOYMENT_GUIDE_FULL.md (comprehensive reference)

---

## 📖 Document Statistics

| Document | Lines | Sections | Checklists |
|----------|-------|----------|------------|
| DEPLOYMENT_QUICK_CARD.md | 200 | 8 phases | 5 |
| WIRING_REFERENCE.md | 300 | 10 | 3 |
| DEPLOYMENT_GUIDE_FULL.md | 1000+ | 12 parts | 10+ |
| SETUP_CHECKLIST.md | 400 | 4 sections | 8+ |
| CSI_SETUP.md | 400 | 8 | 3 |
| CSI_QUICK_START.md | 150 | 5 steps | 1 |
| **Total** | **~2450** | **~40** | **~30+** |

---

## 🎓 Learning Path

**For beginners:**
1. DEPLOYMENT_QUICK_CARD.md (overview)
2. WIRING_REFERENCE.md (hardware)
3. SETUP_CHECKLIST.md (hands-on)
4. Reference others as needed

**For experienced makers:**
1. DEPLOYMENT_QUICK_CARD.md (timeline)
2. WIRING_REFERENCE.md (specifics)
3. Dive into DEPLOYMENT_GUIDE_FULL.md as needed

**For troubleshooting:**
1. DEPLOYMENT_QUICK_CARD.md (quick fixes)
2. DEPLOYMENT_GUIDE_FULL.md Part 9 (detailed)
3. CSI_SETUP.md if camera-specific

---

## 💾 File Organization

```
smartbin_v4/
├── DEPLOYMENT_INDEX.md          ← You are here
├── DEPLOYMENT_QUICK_CARD.md     ← Start here
├── DEPLOYMENT_GUIDE_FULL.md     ← Complete reference
├── WIRING_REFERENCE.md          ← Hardware
├── SETUP_CHECKLIST.md           ← Verification
├── CSI_SETUP.md                 ← Camera details
├── CSI_QUICK_START.md           ← Camera quick start
├── TOF_MIGRATION.md             ← TOF explanation
├── TOF_CSI_CHANGES.md           ← Code changes
│
├── main_pi.py                   ← Main executable
├── config/
│   └── sim_settings.py          ← Configuration (tune here)
├── src/
│   ├── camera_real.py           ← Camera code
│   ├── detect_real.py           ← Detection code
│   └── motors_real.py           ← Motor code
├── tools/
│   ├── diagnose_camera.py       ← Hardware test
│   └── tune_tof.py              ← Camera tuning
└── logs/                        ← Created on first run
```

---

## ✅ Pre-Deployment Checklist

Before starting deployment:

- [ ] All documentation downloaded/accessible
- [ ] Hardware components listed in DEPLOYMENT_GUIDE_FULL.md Part 1.1
- [ ] Wiring diagram (WIRING_REFERENCE.md) printed or accessible
- [ ] Laptop with SSH client
- [ ] Multimeter for testing
- [ ] Raspberry Pi Imager installed on laptop
- [ ] microSD card (32GB+) available
- [ ] All components assembled per WIRING_REFERENCE.md
- [ ] 5V/3A power supply for Pi
- [ ] 12V/5A battery for motors

---

## 🎯 Deployment Success Criteria

After complete deployment, verify:

✓ SmartBin auto-starts on Pi boot  
✓ Camera detects objects reliably  
✓ Motors respond to commands instantly  
✓ Detection latency < 200ms  
✓ Frame rate 8-10 fps  
✓ Temperature stays < 75°C  
✓ Catch success rate > 70%  
✓ Service logs clean errors  
✓ Can SSH in and monitor  

---

## 🎉 You're Ready!

Pick a document above and start with Phase 1 of DEPLOYMENT_QUICK_CARD.md.

**Estimated time:** 2.5-4 hours from here to working SmartBin

Good luck! 🚀

---

**Questions?** Search the documentation or check DEPLOYMENT_GUIDE_FULL.md Part 9 Troubleshooting.
