# Atlas 1.0-6.0 Complete Engineering Log

**Consolidated English Edition for GitHub / PBL Portfolio**

- **Project:** Atlas AI Mentor / Hardware Robot Series
- **Recorder:** Eric
- **Scope:** Smart Plant Care System 1.1; Atlas 1.0, 2.0, 3.0, 4.0, 5.0, and 6.0
- **English edition compiled:** 2026-09-14

## Editorial Note

This is a consolidated English engineering-log edition. Atlas 1.0-5.0 is translated and reorganized from the original moderate-detail engineering log. Atlas 6.0 is added from the project engineering log, development plan, firmware revisions, control-test files, vision/dataset/model-release scripts, final integration programs, and archived project/chat records. Exact dates are used only where the project evidence contains them; later records with no reliable single date are labeled by development period rather than inventing a date.

The document deliberately preserves failures, wrong assumptions, abandoned routes, and debugging decisions because they are part of the engineering evidence.

## Version Evolution Overview

| Version / Project | Core Goal | Main Capabilities | Evidence / Outputs |
|---|---|---|---|
| Smart Plant Care System 1.1 | AI + hardware plant-care prototype | Arduino, sensors, automatic lighting/watering, iterative hardware debugging | Project log, physical prototype, demo evidence |
| Atlas 1.0 | AI Research Mentor Robot foundation | Project Log, mentor advice, research support, basic memory | project_log.txt, memory.json, mentor-response records |
| Atlas 2.0 | Project Management Robot | Project Database, Daily Task, Bug Manager, Weekly Report | atlas2_data.json, weekly_report.txt, bug records |
| Atlas 3.0 | Eric Digital Twin Mentor | Profile, Skill, History, Planner, Emotion, Recommendation | atlas3_data.json, learning plan, mentor recommendations |
| Atlas 4.0 | Multimodal Mentor Robot | Vision, voice input/output, memory, proactive mentor, hardware feedback | atlas4_full_main.py, multimodal logs |
| Atlas 5.0 | Stable Hardware Robot Edition | ESP32, OLED, pan/tilt, LEDs, voice, camera, Safe Mode | Final Python program, JSON/TXT logs, screenshots, demo video |
| Atlas 6.0 | Mobile autonomous hardware robot | L298N drive, dual encoders, closed-loop motion, US-100 sensing, Wi-Fi/TCP safety, C950 AI vision, autonomous recovery, reintegrated expression/voice | ESP32 integrated firmware, Python vision/master programs, model-release scripts, test logs, demo video |

## Chronological Engineering Log

## 1. 2026-07-01 - Smart Plant Care System 1.1 + Atlas 1.0 AI Research Mentor Robot

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Complete the stage record for Smart Plant Care System 1.1 and preserve it as the hardware-learning foundation for Atlas.
- Add automatic Project Log generation to Atlas 1.0.
- Test whether Atlas can read the latest project log and provide mentor-style engineering advice.

**Actual completed work**
- Completed the Smart Plant Care System 1.1 record and linked it to later Atlas hardware learning.
- Upgraded main.py so Atlas can record goals, completed work, problems, solutions, next steps, and mentor advice.
- Saved logs to both memory.json and project_log.txt.
- Validated Mentor Advice and Research Support responses based on recent engineering records.

### 2. Tools, Materials, and Software

Software: Python, main.py, JSON, memory.json, project_log.txt, terminal I/O. Hardware: plant-care prototype, Arduino sensors, soil-moisture and temperature/humidity sensors, PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Formalized the plant-care project as prior experience in sensor reading, wiring, and iterative debugging.
- Created a fixed Project Log schema so later portfolio evidence would not become fragmented.
- Used realistic prompts about completed work and repeated failures to test whether Atlas could respond as an engineering mentor rather than a generic chatbot.

### 4. Problems and Observed Phenomena

- Log storage location was initially unclear, creating a risk that Atlas would not recall previous work.
- Soil-related raw sensor data remained unstable.
- Long debug sessions created a tendency to change several modules at once.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- A single storage path was not robust enough for memory retrieval.
- Sensor instability could come from hardware quality, wiring, sampling range, or insufficient environmental variation.
- Unrecorded failures would cause repeated troubleshooting.

**Attempts**
- Write the same structured log into both memory.json and project_log.txt.
- Keep failed tests as evidence instead of deleting them.
- Reduce the next task to one testable question at a time.

**Final solution / decision:** Atlas 1.0 adopted a fixed-field Project Log, dual-file storage, and mentor advice written back into the log. Unstable plant sensors were deliberately left as a separate hardware-debug task instead of expanding scope.

### 6. Test / Experimental Results

- Automatic Project Log writing worked.
- Atlas generated mentor advice from the latest log.
- Atlas 1.0 became a basic AI mentor with memory, logging, mentor advice, and research-support behavior.

### 7. Remaining Issues

- Plant sensor reliability still required separate testing.
- Cross-day recall still needed validation.

### 8. Next Work Plan

- Test recall of the previous day's Project Log.
- Prepare the transition to Atlas 2.0 project-management functions.

---

## 2. 2026-07-02 (Round 1) - Atlas 2.0 Project Management Robot

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization / Reporting

### 1. Tasks and Completion

**Planned tasks**
- Upgrade Atlas from a logging robot into a project-management robot.
- Implement Project Database, Daily Task, Bug Manager, and Weekly Report.
- Write tasks, bugs, and reports into project_log.txt for traceable evidence.

**Actual completed work**
- Tested the Project Database with Smart Plant Care, Atlas 1.0, and Atlas 2.0 entries.
- Created and reviewed a Daily Task.
- Recorded and resolved an OpenCV face-detection bug in Bug Manager.
- Generated a Weekly Report summarizing projects, tasks, bugs, and mentor judgments.

### 2. Tools, Materials, and Software

Software: Python, atlas2_main.py and staged scripts, JSON files, project_log.txt, OpenCV. Hardware: PC and camera for vision-bug testing.

### 3. Process Record - Key Operations / Parameters / Steps

- Validated Project Database log writing and project updates.
- Created task fields for date, project, plan, estimated time, priority, reason, and status.
- Used Bug Manager to document a real false-detection problem and its fix.
- Generated a Weekly Report to test the complete management loop.

### 4. Problems and Observed Phenomena

- An accidental terminal input polluted a project status field.
- Early OpenCV person detection remained active after Eric left the frame.
- It was necessary to verify that the Weekly Report actually aggregated all data sources.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Terminal input validation was weak.
- Person detection was sensitive to background, range, and lighting.
- Module data structures were still distributed.

**Attempts**
- Corrected the project status and progress back to completed / 100%.
- Switched the unstable detection direction toward face detection.
- Repeated logging tests for all four management modules.

**Final solution / decision:** Kept the mistaken input as authentic debug evidence, corrected the project record afterward, changed the vision test to face detection, and used the Weekly Report as the stage-closing artifact.

### 6. Test / Experimental Results

- All four Atlas 2.0 management functions ran successfully.
- Daily Task and review worked.
- Bug Manager supported add/search/update/summary operations.
- Weekly Report produced project, task, bug, and next-week summaries.

### 7. Remaining Issues

- Project Database input validation could be stronger.
- Chat-history writing into project_log still needed testing.

### 8. Next Work Plan

- Merge the separated Atlas 2.0 modules into one main program.
- Begin Atlas 3.0 profile and long-term growth modeling.

---

## 3. 2026-07-02 (Round 2) - Atlas 2.0 Integrated Build and Stage Closeout

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization / Reporting

### 1. Tasks and Completion

**Planned tasks**
- Merge Project Database, Daily Task, Bug Manager, and Weekly Report.
- Add a Demo-video task and regenerate the Weekly Report.
- Test data migration and consolidated logging.

**Actual completed work**
- Created atlas2_data.json and migrated data from the earlier separated JSON files.
- Ran the integrated atlas2_main.py one-click overview.
- Added an Atlas 2.0 demo-video Daily Task.
- Recorded the unresolved project_log chat-record issue as a Bug.
- Generated a corrected Weekly Report showing Atlas 2.0 at 100% completion.

### 2. Tools, Materials, and Software

Software: Python, atlas2_main.py, atlas2_data.json, project_log.txt, weekly_report.txt. Hardware: PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Migrated legacy project/task/bug/report records before launching the integrated program.
- Used the one-click overview as a stage-level demonstration.
- Preserved the unresolved chat-log issue inside Bug Manager instead of hiding it.

### 4. Problems and Observed Phenomena

- Multiple JSON files were difficult to maintain.
- Chat content was still not being written into project_log.
- Demo filming was only partially complete.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- The project grew module-by-module, producing fragmented files.
- Chat logging and normal project logging did not share one write path.
- Demo filming required synchronized software, hardware, and narration.

**Attempts**
- Use a unified main program and consolidated JSON.
- Keep unresolved cross-version issues visible in Bug Manager.
- Regenerate reports after correcting bad records.

**Final solution / decision:** Atlas 2.0 was accepted as functionally complete. The remaining chat-log issue was preserved as a known cross-version limitation rather than blocking the core project-management functions.

### 6. Test / Experimental Results

- Atlas 2.0 progress was corrected to 100%.
- The integrated demo view could show projects, tasks, bugs, and reports.
- The Weekly Report retained real bug-fix evidence.

### 7. Remaining Issues

- Chat-history logging remained unresolved.
- Demo video still required completion.

### 8. Next Work Plan

- Start Atlas 3.0 Profile, Skill Database, and Project History.
- Carry Atlas 2.0 management capability into the personalized mentor layer.

---

## 4. 2026-07-03 (Round 1) - Atlas 3.0 Digital Twin Mentor Robot - Profile / Skill / History

**Recorder:** Eric  
**Phase:** System Design / Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Build an Eric Profile with age, goals, projects, interests, strengths, and weaknesses.
- Create a Skill Database that can influence recommendations.
- Create Project History linking the plant system and Atlas 1.0-3.0.

**Actual completed work**
- Completed Eric Profile and identity-aware responses.
- Created Skill Database values including Arduino 95, Python 80, OpenCV 75, YOLO 60, and ROS2 0.
- Atlas could recommend ROS2 instead of repeating basic Arduino.
- Completed Project History explaining how earlier projects contributed skills to later versions.

### 2. Tools, Materials, and Software

Software: Python, profile.json, skills.json, history.json, project_log.txt. Hardware: PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Locked Eric's long-term target as AI Systems Engineer and project-based learning as the preferred learning style.
- Used scored skills so mentor recommendations were data-driven.
- Tested project-history search and cross-project skill transfer explanations.

### 4. Problems and Observed Phenomena

- Generic greetings were not sufficiently personalized.
- Exact keyword matching failed on some near-synonyms.
- ROS2 was clearly identified as the largest skill gap.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Without Profile, Skill, and History, recommendations would remain generic.
- The current search used simple lexical matching rather than semantic retrieval.
- Eric already had enough Arduino/Python/OpenCV experience to justify a systems-level next step.

**Attempts**
- Test each database independently with fixed questions.
- Keep semantic-search improvement as a later enhancement.
- Use the data chain to justify the ROS2 recommendation.

**Final solution / decision:** Atlas 3.0 shifted from feature accumulation to a data-driven Eric Digital Twin: first know who Eric is, what he knows, and what he has built; then recommend the next learning step.

### 6. Test / Experimental Results

- Eric Profile worked.
- Skill Database worked and produced a ROS2 recommendation.
- Project History explained skill transfer from the plant project into Atlas.

### 7. Remaining Issues

- Near-synonym project search still needed improvement.
- ROS2 had been identified but not yet learned.

### 8. Next Work Plan

- Continue with Learning Planner, Emotion Memory, and Mentor Recommendation.

---

## 5. 2026-07-03 (Round 2) - Atlas 3.0 Digital Twin Mentor Robot - Planner / Emotion / Recommendation / Data Integration

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization / Reporting

### 1. Tasks and Completion

**Planned tasks**
- Generate a daily learning plan.
- Record engineering emotion/debug state.
- Generate mentor recommendations from Profile + Skill + History + Planner + Emotion.
- Integrate Atlas 1.0-3.0 data.

**Actual completed work**
- Built a ROS2-oriented Learning Planner.
- Recorded a real Arduino sensor failure inside Emotion Memory.
- Generated a recommendation explaining why ROS2 was the next priority.
- Created atlas3_data.json and additional integrated/unified JSON files.

### 2. Tools, Materials, and Software

Software: Python, learning_plan.json, emotion_memory.json, mentor_recommendation.json, atlas3_data.json, atlas_unified_data.json. Hardware: PC; Arduino sensor hardware referenced in the debug record.

### 3. Process Record - Key Operations / Parameters / Steps

- Read Profile, Skill Database, and Project History in sequence.
- Generated a plan and exposed the reasoning behind it.
- Logged frustration as engineering-state context, not as a psychological diagnosis.
- Migrated several JSON sources into unified structures.

### 4. Problems and Observed Phenomena

- Soil/temperature-humidity sensor data was still unstable.
- Fragmented JSON files could make recommendations incomplete.
- The recommendation system needed evidence that results were not random.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Hardware quality/wiring/power could explain sensor instability.
- Fragmented context weakened recommendation quality.
- Recommendations needed a transparent Profile -> Skill -> History -> Plan -> Emotion reasoning chain.

**Attempts**
- Record hardware failure as Emotion Memory.
- Display recommendation logic.
- Consolidate data sources.

**Final solution / decision:** Completed a six-part Atlas 3.0 loop: Profile, Skill, History, Planner, Emotion, Recommendation, integrated into unified data structures.

### 6. Test / Experimental Results

- Digital Twin foundation completed.
- Atlas could explain why ROS2 was recommended.
- Cross-version data migration became possible.

### 7. Remaining Issues

- ROS2 learning plan had not yet been executed.
- Hardware sensor issues remained separate.
- Vision, voice, and hardware feedback still needed Atlas 4.0 integration.

### 8. Next Work Plan

- Enter Atlas 4.0 multimodal development.

---

## 6. 2026-07-04 (Round 1) - Atlas 4.0 Multimodal Mentor Robot - Proactive Mentor / Voice / Hardware Feedback

**Recorder:** Eric  
**Phase:** Hardware Integration / Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Add a proactive Morning Brief based on long-term memory.
- Test voice output.
- Test physical hardware feedback through serial commands.

**Actual completed work**
- Completed Proactive Mentor using atlas_unified_data.json.
- Voice output successfully spoke greetings, Morning Briefs, and custom text.
- Established a working COM4 hardware connection after serial debugging.
- Tested STATUS, HAPPY, WARNING, and NOD commands.

### 2. Tools, Materials, and Software

Software: Python, pyttsx3, pyserial, atlas4_proactive_mentor.py, atlas4_hardware_feedback.py, atlas4_full_main.py. Hardware: Arduino/CH340 serial board, LEDs, OLED, servo, USB cable, PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Generated Morning Brief from long-term data.
- Tested TTS independently.
- Tried COM4/COM6, documented FileNotFoundError/PermissionError, then closed competing serial tools.
- Used PING/PONG before behavior commands.

### 4. Problems and Observed Phenomena

- COM4/COM6 sometimes failed to open.
- PermissionError indicated another process owned the port.
- Sometimes no serial device was detected.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Arduino IDE Serial Monitor, plotter, or another Python process could own the port.
- Configured COM port could differ from the real device.
- USB cable, drivers, and reconnect state affected detection.

**Attempts**
- List ports first.
- Close any serial monitor.
- Confirm PING/PONG before behavior testing.

**Final solution / decision:** Established a repeatable serial-debug sequence: detect device -> close competing process -> PING/PONG -> send hardware commands. This pattern was reused in Atlas 5.0.

### 6. Test / Experimental Results

- Proactive Mentor generated Morning Briefs.
- Voice Output worked.
- Hardware feedback could be controlled through COM4.
- Atlas 4.0 formed a memory -> proactive advice -> voice -> hardware-feedback chain.

### 7. Remaining Issues

- Hardware still depended on stable serial access.
- Vision, voice input/output, memory, and hardware still needed one integrated main program.

### 8. Next Work Plan

- Build Atlas 4.0 Full Main and the Atlas 1.0-4.0 integrated program.

---

## 7. 2026-07-04 (Round 2) - Atlas 4.0 Full Main + Atlas 1.0-4.0 Integrated Program

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization / Reporting

### 1. Tasks and Completion

**Planned tasks**
- Integrate Vision, Voice Input, Voice Output, Memory, Proactive Mentor, and Hardware Feedback.
- Combine major capabilities from Atlas 1.0-4.0.
- Validate vision, voice, and overall status reporting.

**Actual completed work**
- Ran Atlas 4.0 Full status overview.
- Validated vision frame counts with Eric present/absent.
- Completed repeated voice-output tests.
- Launched the Atlas 1.0-4.0 master program and displayed version capabilities and data statistics.

### 2. Tools, Materials, and Software

Software: Python, OpenCV, pyttsx3, pyserial, atlas4_full_main.py, atlas_all_versions_main.py, atlas_unified_data.json. Hardware: USB camera, hardware-feedback controller, PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Checked dependency state and database/config paths.
- Ran vision and voice separately before the all-version wrapper.
- Kept camera and recording optional in the main demo to reduce simultaneous failure points.

### 4. Problems and Observed Phenomena

- Vision depended on reliable camera opening.
- Hardware feedback still risked serial-port conflicts.
- Older version data formats differed.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Multimodal integration increased the number of possible failure sources.
- Legacy data required normalization.
- COM port changes remained an external dependency.

**Attempts**
- Integrate modules in stages.
- Use a unified menu for 1.0-4.0 capabilities.
- Keep a text-only overview path that does not force all peripherals online.

**Final solution / decision:** Created an Atlas 1.0-4.0 software backbone with a unified menu and optional multimodal tests.

### 6. Test / Experimental Results

- Atlas 4.0 multimodal main program was basically complete.
- Atlas 1.0-4.0 overview and statistics worked.
- The software architecture was ready for Atlas 5.0 physical-system engineering.

### 7. Remaining Issues

- Physical hardware stability still depended on the controller/serial link.
- Atlas 5.0 needed a hardware architecture rather than another software-only feature layer.

### 8. Next Work Plan

- Archive 1.0-4.0 evidence and begin Atlas 5.0 Hardware Robot Edition.

---

## 8. 2026-07-05 - Atlas 5.0 Hardware Robot Edition - Architecture and Engineering Documentation

**Recorder:** Eric  
**Phase:** System Design / Documentation

### 1. Tasks and Completion

**Planned tasks**
- Redefine 5.0 as a hardware-engineering system rather than a repeat of 4.0 features.
- Design the PC/controller/servo/OLED/LED/power/common-ground architecture.
- Define Serial Protocol v5, behavior states, and file structure.

**Actual completed work**
- Confirmed the revised Atlas 5.0 plan.
- Defined IDLE, LISTENING, THINKING, SUCCESS, ENCOURAGE, WARNING, and ERROR.
- Mapped each state to LEDs, OLED, head motion, voice style, and logging.
- Prepared an engineering folder model: docs, firmware, python, data, logs.

### 2. Tools, Materials, and Software

Software/documentation: Word, Markdown, Python project-layout draft, Serial Protocol v5 draft. Planned hardware: ESP32/Arduino, pan/tilt servos, OLED, LEDs, external power, common GND.

### 3. Process Record - Key Operations / Parameters / Steps

- Designed the system before adding new wiring.
- Changed hardware control from isolated commands to state-machine orchestration.
- Defined observable behavior for each state.
- Created documentation and file-structure standards.

### 4. Problems and Observed Phenomena

- Early plans risked turning 5.0 into another pile of 4.0 features.
- Without a state machine, LED/OLED/servo behavior would remain fragmented.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Atlas 4.0 already demonstrated multimodal software; 5.0 needed physical reliability.
- Behavior needed a common abstraction layer.

**Attempts**
- Define state table first.
- Define protocol and file structure before hardware integration.
- Convert earlier logs into formal engineering documentation.

**Final solution / decision:** Locked the design principle: PC/Python handles voice, camera, and logic; ESP32 handles OLED/LED/servo behavior; both communicate through serial commands and READY_FOR_NEXT_COMMAND.

### 6. Test / Experimental Results

- Architecture direction became explicit.
- State-machine foundation was complete.
- Engineering standards for later integration were established.

### 7. Remaining Issues

- ESP32 head hardware had not yet been integrated.
- Serial Protocol v5 still required real testing.

### 8. Next Work Plan

- Build the pan/tilt head and basic ESP32 control.

---

## 9. 2026-07-06 - Atlas 5.0 Stage 2 - Two-Axis Pan/Tilt Head and ESP32 Basic Control

**Recorder:** Eric  
**Phase:** Hardware Build / Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Build the pan/tilt head.
- Use ESP32 instead of Arduino Uno as the main 5.0 controller.
- Test PING, LEDTEST, ARM, CENTER, LEFT, RIGHT, UP, DOWN, NOD, SHAKE, and TEST.

**Actual completed work**
- Completed the two-axis head; OLED was physically mounted as the face.
- Locked an initial pin plan: pan GPIO18, tilt GPIO19, green GPIO25, yellow GPIO26, red GPIO27.
- Powered servos from an independent 4xAA holder while ESP32 remained USB powered.
- Validated basic LED and servo commands.

### 2. Tools, Materials, and Software

Software: Arduino IDE, ESP32Servo, Serial Monitor, Stage 2 firmware. Hardware: ESP32, two small servos, pan/tilt structure, LEDs, 4xAA holder, jumper wires, OLED.

### 3. Process Record - Key Operations / Parameters / Steps

- Moved from the Arduino Uno direction to ESP32.
- Powered servo red wires from the battery holder and tied battery negative to ESP32 GND.
- Used ARM/DISARM around head actions.
- Tested each motion command separately.

### 4. Problems and Observed Phenomena

- Uno-based power/connection risk was undesirable.
- Tilt servo initially had mechanical-direction/horn issues.
- Servo current could not reliably come from ESP32 3V3/5V.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Servo startup current was high.
- Mechanical neutral and software 90-degree center were not necessarily aligned.
- Tilt axis carried more load.

**Attempts**
- Reinstall/calibrate the tilt servo.
- Use an independent 4xAA servo supply.
- Validate each primitive command independently.

**Final solution / decision:** Adopted ESP32 + independent servo power + common ground + ARM/DISARM safety. Stage 2 intentionally stayed focused on basic motion rather than voice/camera/OLED integration.

### 6. Test / Experimental Results

- Pan/tilt basic control passed.
- Left/right/up/down/nod/shake motions worked.
- The hardware base for later behavior firmware was established.

### 7. Remaining Issues

- Power and cable routing needed mechanical stabilization.
- Primitive actions still needed state-level behavior logic.

### 8. Next Work Plan

- Enter Stage 3 power/cable engineering and Stage 4 behavior firmware.

---

## 10. 2026-07-07 - Atlas 5.0 Stage 3-4 - Power/Cable Engineering and Behavior Firmware v2

**Recorder:** Eric  
**Phase:** Hardware Build / Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Fix the battery holder and critical cables.
- Implement stable IDLE/LISTENING/THINKING/SUCCESS/ENCOURAGE/WARNING/ERROR behavior firmware.
- Add READY_FOR_NEXT_COMMAND handshake.

**Actual completed work**
- Completed battery and cable securing, wire labels, and U-shaped slack around the moving head.
- Passed TEST20/TEST50 stability checks.
- Completed Behavior Firmware v2 Stable with START, DONE, and READY_FOR_NEXT_COMMAND responses.
- Validated all main behavior states and BEHAVIOR_TEST.

### 2. Tools, Materials, and Software

Software: Arduino IDE, ESP32Servo, atlas5_stage4_behavior_firmware_v2_stable.ino, Serial Monitor. Hardware: ESP32, pan/tilt servos, LEDs, 4xAA holder, cable labels and mounting materials.

### 3. Process Record - Key Operations / Parameters / Steps

- Stabilized hardware before adding software complexity.
- Uploaded behavior firmware and sent one state command at a time.
- Waited for READY_FOR_NEXT_COMMAND before sending the next action.

### 4. Problems and Observed Phenomena

- Some old state actions were visually weak.
- Blocking delays and missing start/end messages made it difficult to know whether a command was still executing.
- Tight cables affected head motion.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Command timing and servo execution were unsynchronized.
- Without explicit protocol feedback, software/hardware faults looked similar.
- Pan/tilt mechanics required cable slack.

**Attempts**
- Add START/DONE/READY messages.
- Make state feedback more visible.
- Run chained BEHAVIOR_TEST.

**Final solution / decision:** Established the low-level behavior protocol: while ESP32 executes an action, Python/user waits for READY_FOR_NEXT_COMMAND. Mechanical cable management reduced motion interference.

### 6. Test / Experimental Results

- Power/cable engineering completed.
- Behavior Firmware v2 ran stably.
- Atlas 5.0 gained unified state feedback.

### 7. Remaining Issues

- Python still needed to take over the serial protocol from manual Serial Monitor use.

### 8. Next Work Plan

- Enter Stage 5-8 Python HAL, state machine, simulated brain, and text-dialogue flow.

---

## 11. 2026-07-08 - Atlas 5.0 Stage 5-8 - Python HAL, State Machine, Brain Simulation, Dialogue Flow

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Control ESP32 from Python.
- Build a Python behavior state machine and simulated input layer.
- Create a text dialogue flow that triggers hardware states.

**Actual completed work**
- Completed Python HAL PING and behavior tests.
- Built the behavior-state-machine menu.
- Built Brain Simulation mapping text intents to hardware states.
- Completed Dialogue Flow so typed input produced replies and physical feedback.

### 2. Tools, Materials, and Software

Software: Python, pyserial, atlas5_hal_ping_test.py, atlas5_hal_behavior_test.py, atlas5_stage6_behavior_state_machine.py, atlas5_stage7_brain_simulation.py, atlas5_stage8_dialogue_flow.py. Hardware: ESP32, pan/tilt, LEDs, 4xAA holder.

### 3. Process Record - Key Operations / Parameters / Steps

- Built the HAL first: open serial, send commands, wait for READY.
- Validated PING/LEDTEST/ARM before higher layers.
- Added a simple intent mapper and dialogue log only after HAL and state machine worked.

### 4. Problems and Observed Phenomena

- Python could not open the port while Serial Monitor was active.
- Sending commands without waiting for READY caused missed behavior.
- Intent recognition was rule-based rather than an LLM.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Only one process can own a serial port.
- ESP32 actions need execution time.
- The engineering goal was a stable closed loop, not open-domain conversation.

**Attempts**
- Close Serial Monitor before Python.
- Honor READY_FOR_NEXT_COMMAND.
- Validate text input before microphone integration.

**Final solution / decision:** Created a layered system: HAL -> State Machine -> Brain Simulation -> Dialogue Flow. Each layer was validated before integration.

### 6. Test / Experimental Results

- Python reliably controlled ESP32.
- Text input -> intent -> behavior state -> hardware feedback worked.
- The system was ready for real voice input.

### 7. Remaining Issues

- Real microphone input was not integrated yet.
- Voice output and camera were still separate.

### 8. Next Work Plan

- Enter Stage 9-10 real voice-input preparation and ASR selection.

---

## 12. 2026-07-09 - Atlas 5.0 Stage 9-10 - Real Voice Input Preparation, Vosk Failure, and Route Adjustment

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Add microphone recording and LISTENING state.
- Try Vosk offline speech recognition.
- Fall back to the proven Atlas 4.0 voice stack if Vosk is unstable.

**Actual completed work**
- Completed Stage 9 microphone recording and WAV saving with manual confirmed text.
- Tried Vosk but hit MODEL_PATH and model-creation errors.
- Confirmed Python 3.12 direction but model-path/model-structure problems remained.
- Decided to abandon Vosk for this version and reuse sounddevice + SpeechRecognition + pyttsx3.

### 2. Tools, Materials, and Software

Software: Python, sounddevice, scipy, SpeechRecognition, pyttsx3, Vosk (attempted then abandoned), PyCharm. Hardware: PC microphone/speaker, ESP32, pan/tilt, LEDs.

### 3. Process Record - Key Operations / Parameters / Steps

- First completed a recording layer without automatic recognition.
- Tried Vosk with expected model subdirectories.
- Traced NameError and model-load failures.
- Compared the failing route with previously successful Atlas 4.0 voice code.

### 4. Problems and Observed Phenomena

- NameError: MODEL_PATH is not defined.
- After fixing definition order, Vosk still failed to create a model.
- Local model path/structure compatibility remained a high-risk dependency.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- MODEL_PATH was referenced too early.
- Vosk failure could involve path, structure, model integrity, or environment compatibility.
- Offline ASR added complexity unrelated to the immediate project goal.

**Attempts**
- Check Python version and model path.
- Attempt a path fix.
- Reuse the already-proven online SpeechRecognition route.

**Final solution / decision:** Redefined Stage 10 as Stage 10B using sounddevice recording, Google SpeechRecognition, and pyttsx3 instead of Vosk.

### 6. Test / Experimental Results

- Stage 9 recording flow completed.
- The recognition architecture was simplified to a known-good approach.
- The route was ready for the next day's full voice loop.

### 7. Remaining Issues

- Stage 10B integration remained.
- Google SpeechRecognition required network access.

### 8. Next Work Plan

- Build the real voice input + voice output + ESP32 behavior loop.

---

## 13. 2026-07-10 (Morning) - Atlas 5.0 Stage 10B - Google Voice + TTS + ESP32 Behavior Loop

**Recorder:** Eric  
**Phase:** Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Reuse the proven Atlas 4.0 voice approach inside Atlas 5.0.
- Implement speech -> recognition -> reply -> TTS -> ESP32 behavior.
- Test English and Chinese input.

**Actual completed work**
- Ran Stage 10B using SpeechRecognition and pyttsx3.
- Successfully recognized English and Chinese examples.
- Logged several intent classes including project questions, self-introduction, encouragement, normal questions, and greeting.
- Triggered SUCCESS and ENCOURAGE hardware states from recognized speech.

### 2. Tools, Materials, and Software

Software: Python, sounddevice, scipy, numpy, SpeechRecognition, pyttsx3, pyserial, atlas5_stage10b_google_voice_and_tts.py. Hardware: PC microphone/speaker, ESP32, pan/tilt, LEDs, 4xAA holder.

### 3. Process Record - Key Operations / Parameters / Steps

- Performed PING, LEDTEST, ARM, and IDLE before voice interaction.
- Used LISTENING during recording and THINKING during recognition.
- Mapped intents to behavior states and speech responses.

### 4. Problems and Observed Phenomena

- At one point speech worked while hardware did not respond.
- ESP32 body firmware may have been overwritten by another test sketch.
- Serial Monitor could still block Python access.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- ESP32 only runs the most recently flashed firmware.
- If body firmware is replaced, Python state commands are no longer recognized.
- Serial ownership conflicts remain possible.

**Attempts**
- Validate voice separately.
- Check power, wiring, and serial ownership.
- Reflash the stable ESP32 body firmware.

**Final solution / decision:** Restored and preserved stable body firmware. Python became responsible for sending state commands; ESP32 remained responsible for LED and servo behavior.

### 6. Test / Experimental Results

- All Stage 10B tests passed.
- Atlas 5.0 achieved a real voice input + voice output + hardware behavior loop.
- Successful dialogue records were generated.

### 7. Remaining Issues

- Local memory, OLED state display, and camera input still needed integration.

### 8. Next Work Plan

- Enter Stage 11 memory and Stage 12 OLED/camera integration.

---

## 14. 2026-07-10 (Afternoon) - Atlas 5.0 Stage 11-12 - Local Memory, OLED, Camera, and Safe Mode

**Recorder:** Eric  
**Phase:** Hardware Integration / Code Debugging / Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Add local JSON memory.
- Integrate OLED state display.
- Integrate the EMEET C950 through PC/OpenCV.
- Fix servo twitching and camera-window input issues.

**Actual completed work**
- Built a local memory record with student_name, dialogue_count, last_user_text, last_intent, last_emotion, last_topic, and last_reply.
- Connected OLED and flashed OLED-capable body firmware.
- Diagnosed the head pointing downward after ARM as a mechanical servo-neutral problem.
- Opened the C950 successfully through OpenCV on the PC.
- Built a terminal-control Safe Mode version for camera + hardware behavior.

### 2. Tools, Materials, and Software

Software: Python, OpenCV, pyserial, Arduino IDE, Adafruit SSD1306/GFX, ESP32Servo, atlas5_stage12c_camera_terminal_control_safe.py. Hardware: ESP32, OLED, C950, pan/tilt, LEDs, 4xAA holder, PC.

### 3. Process Record - Key Operations / Parameters / Steps

- Tested OLED first without camera.
- Tested body states after enabling servo power.
- Re-centered the tilt servo mechanically around the software neutral.
- Tested camera independently before camera + ESP32 integration.
- Changed behavior to ARM -> ACTION -> DISARM to reduce continuous servo holding.
- Moved command input from OpenCV-window keys to the PyCharm terminal.

### 4. Problems and Observed Phenomena

- OLED/head pointed downward after ARM.
- Servos twitched continuously during camera-control tests.
- Initial actions worked but later terminal input sometimes seemed ignored.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Mechanical tilt neutral did not match software 90 degrees.
- Small servos were being held energized under OLED load.
- The old camera-window version only listened for keys when the OpenCV window had focus.

**Attempts**
- Reinstall the horn at software neutral or calibrate the front angle.
- Use Safe Mode with short ARM windows.
- Use terminal input instead of OpenCV-window key focus.

**Final solution / decision:** Adopted OLED body firmware + PC-hosted C950 + Python terminal-control Safe Mode. This preserved vision preview while reducing servo stress and input-focus failures.

### 6. Test / Experimental Results

- OLED + Python control passed.
- C950 opened successfully.
- Terminal commands triggered hardware states.
- Atlas gained a vision-input foundation + OLED status + safer physical behavior.

### 7. Remaining Issues

- Automatic visual recognition was not yet the final control path.
- Servos should not remain ARM-held for long periods.

### 8. Next Work Plan

- Integrate the final voice, camera, OLED, LED, pan/tilt, safe actions, and logging program.

---

## 15. 2026-07-10 (Evening) - Atlas 5.0 Final Stable Program v1 + Atlas 1.0-5.0 Archive

**Recorder:** Eric  
**Phase:** Code Integration / Test Optimization / Reporting

### 1. Tasks and Completion

**Planned tasks**
- Integrate camera and voice into the final Atlas 5.0 program.
- Integrate Atlas 1.0-5.0 capabilities into one master program.
- Merge JSON and TXT records.
- Create the complete engineering-log archive.

**Actual completed work**
- Completed Atlas 5.0 Final Stable Program v1 with camera preview, terminal menu, real audio recording, SpeechRecognition, pyttsx3, ESP32 OLED/LED/pan-tilt control, and Safe Mode.
- Tested English and Chinese dialogue with all major physical modules running together.
- Saved camera snapshots.
- Integrated the all-version main program.
- Merged Stage 10B and Final Stable JSON records into 11 total runtime records.
- Combined TXT records and prepared the engineering-log document.

### 2. Tools, Materials, and Software

Software: Python, OpenCV, sounddevice, SpeechRecognition, pyttsx3, pyserial, JSON, TXT, Word/docx, atlas_1_2_3_4_5_full_main.py, atlas_all_versions_final_data.json. Hardware: ESP32, OLED, C950, PC microphone/speaker, pan/tilt, LEDs, 4xAA holder.

### 3. Process Record - Key Operations / Parameters / Steps

- Ran PING/LEDTEST/OLEDTEST before enabling the servo battery.
- Used ARM -> IDLE -> DISARM as the initial physical check.
- Kept the camera window open but used terminal commands.
- Saved recognized text, intent, reply, state, and snapshot paths.
- Integrated 1.0-4.0 and 5.0 through an outer master menu.

### 4. Problems and Observed Phenomena

- Multi-version code and data were scattered.
- The final multimodal program had many peripheral dependencies.
- Google SpeechRecognition still required Internet access.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Five project versions naturally produced many files and schemas.
- Any occupied/unplugged peripheral could fail in a multimodal demo.
- ASR was cloud-backed rather than offline.

**Attempts**
- First stabilize the 5.0 final program independently.
- Merge JSON, then TXT, then the engineering log.
- Keep Safe Mode to protect servos.

**Final solution / decision:** Locked the Atlas 5.0 stable demonstration architecture: ESP32 body firmware remains stable; Python owns voice/camera/menu/logging/data integration; physical actions are triggered by state commands and followed by DISARM.

### 6. Test / Experimental Results

- Atlas 5.0 final integration passed.
- Atlas 1.0-5.0 master program existed.
- JSON/TXT records were archived.
- The project now had a strong evidence base for code, data, engineering logs, and video.

### 7. Remaining Issues

- Automatic face/motion detection remained future work.
- ROS2 remained a major next-system upgrade.
- Final demo filming and portfolio packaging remained.

### 8. Next Work Plan

- Film the Atlas 5.0 final demo.
- Protect the 5.0 archive as read-only.
- Begin Atlas 6.0 as a new development branch rather than editing the stable 5.0 build.

---

## 16. 2026-07-13 to 2026-07-19 - Atlas 6.0 Stage 0-2 - Freeze Atlas 5.0, Install Robotics Environment, Build Engineering Skeleton

**Recorder:** Eric  
**Phase:** Archive Protection / Environment Setup / System Architecture

### 1. Tasks and Completion

**Planned tasks**
- Preserve Atlas 5.0 as a stable, read-only baseline.
- Create a separate Atlas_6.0_Development workspace.
- Prepare WSL2, Ubuntu 24.04, ROS2 Jazzy, Arduino/ESP32 tooling, Git, and a documented engineering structure.
- Separate high-level robotics planning from ESP32 real-time control.

**Actual completed work**
- Created a protected 5.0 archive and a separate 6.0 development copy.
- Confirmed the Windows + WSL2 + Ubuntu 24.04 + ROS2 Jazzy direction.
- Established the 6.0 project skeleton with docs, tests, test_data, ESP32 firmware folders, and development rules.
- Defined early architecture: ROS2 for high-level organization/safety/logging, ESP32 for GPIO/PWM/encoder/sensor real-time work, and a safety layer with final veto authority.

### 2. Tools, Materials, and Software

Software: Windows, WSL2, Ubuntu 24.04, ROS2 Jazzy, Arduino IDE, ESP32 board support, Git, Python tools, project Markdown documentation. Hardware: existing Atlas 5.0 head preserved; mobile-base hardware not yet powered.

### 3. Process Record - Key Operations / Parameters / Steps

- Kept Atlas 5.0 files outside the active 6.0 development path.
- Created engineering standards for hardware baseline, GPIO map, safety, communication protocol, acceptance tests, decision log, changelog, and engineering log.
- Intentionally prevented early 6.0 scope from expanding into SLAM or a large AI-agent architecture before the mobile base was reliable.

### 4. Problems and Observed Phenomena

- Atlas 5.0 was a stable interactive robot but not yet a reliable mobile robotics platform.
- ROS2 knowledge and mobile-base engineering had to be added without damaging the working 5.0 system.
- Hardware details and GPIO assignments were not yet sufficiently confirmed for powered motor testing.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Modifying the 5.0 archive would destroy the project baseline.
- Mixing high-level software, motor power, and unverified GPIO at the same time would create too many variables.
- An engineering-documentation layer was needed to keep later decisions reproducible.

**Attempts**
- Freeze 5.0; develop only in a copied 6.0 branch.
- Document before wiring.
- Use staged acceptance gates and full replacement files rather than ad-hoc code patches.

**Final solution / decision:** Atlas 6.0 began as a new mobile-robot engineering program with a protected predecessor, reproducible workspace, formal safety rules, and an explicit real-time / high-level architecture split.

### 6. Test / Experimental Results

- 5.0 remained protected.
- ROS2/Ubuntu/Git/Arduino development environment was prepared.
- 6.0 engineering skeleton and documentation standards were established.

### 7. Remaining Issues

- Mobile chassis was not yet powered.
- Final motor driver, encoder configuration, and power architecture still required real testing.

### 8. Next Work Plan

- Proceed to chassis assembly and software-only ROS2 fundamentals while keeping the motor system unpowered.

---

## 17. 2026-07-22 - Atlas 6.0 Stage 3 + Parallel ROS2 Fundamentals - Mechanical Chassis and Software Pre-Learning

**Recorder:** Eric  
**Phase:** Mechanical Assembly / ROS2 Learning / Software-Only Testing

### 1. Tasks and Completion

**Planned tasks**
- Complete the empty mobile chassis without powering the motors.
- Measure the physical robot geometry and verify free mechanical movement.
- Use the waiting time to learn ROS2 nodes, topics, publishers/subscribers, launch files, and graph inspection without controlling the robot.

**Actual completed work**
- Assembled the mobile base and manually checked forward/backward/turning motion.
- Measured wheel/chassis geometry for later control work.
- Identified a small acrylic-chassis crack and treated it as a structural item to monitor before powered tests.
- Loaded the ROS2 Jazzy environment, used the Atlas workspace, and validated simple command_node -> display_node communication as a software-only exercise.

### 2. Tools, Materials, and Software

Software: Ubuntu 24.04, ROS2 Jazzy, colcon workspace, rosdep, Git, Python ROS2 nodes. Hardware: unpowered chassis, wheels, caster, motors, acrylic plates.

### 3. Process Record - Key Operations / Parameters / Steps

- Kept the mobile base unpowered while checking wheel alignment, friction, caster height, and structure.
- Ran ROS2 communication exercises separately from hardware so a ROS learning mistake could not command the motors.
- Used Git and workspace structure as part of the engineering workflow rather than treating code files as isolated sketches.

### 4. Problems and Observed Phenomena

- The chassis had an acrylic crack that needed monitoring.
- An initially available 7.5 A automotive fuse was recognized as inappropriate for the intended protection target.
- ROS2 exercises were ahead of the physical mainline and therefore could not be treated as real robot integration.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Mechanical damage must be separated from electrical/software debugging.
- A protection device is only useful when its rating matches the expected current and wiring.
- Software simulation and conceptual learning are not proof of powered hardware behavior.

**Attempts**
- Temporarily stabilize and monitor the acrylic area; do not use it as proof of structural readiness by itself.
- Switch the intended protection direction to an appropriately rated 2 A fuse/holder.
- Label ROS2 work as parallel preparation, not as completion of the hardware stages.

**Final solution / decision:** Completed the unpowered chassis and a software-only ROS2 learning block while preserving the project rule that real motor stages require separate physical acceptance.

### 6. Test / Experimental Results

- Chassis could be manually moved without obvious binding.
- ROS2 publisher/subscriber fundamentals worked.
- The power-protection plan was corrected before powered testing.

### 7. Remaining Issues

- Powered motor behavior remained unverified.
- The acrylic crack required continued observation.
- Final motor driver/power wiring still needed confirmation.

### 8. Next Work Plan

- Prepare safe powered motor testing with current protection, physical disconnect capability, and staged measurements.

---

## 18. 2026-07-23 to 2026-07-27 - Atlas 6.0 Stage 4 Preparation - Power, Protection, Motor/Encoder Identification

**Recorder:** Eric  
**Phase:** Electrical Safety Preparation / Hardware Identification

### 1. Tasks and Completion

**Planned tasks**
- Prepare the mobile base for the first powered test without yet driving the robot on the ground.
- Confirm motor wiring, encoder wire groups, driver pins, power isolation, and emergency-stop strategy.
- Keep encoder signals isolated until basic motor direction is proven.

**Actual completed work**
- Prepared a 2 A fuse direction, fuse holder, initial approximately 6 V motor-power concept, and a self-locking emergency-stop idea.
- Inspected driver and motor wiring.
- Confirmed that the Hiwonder six-wire motor assembly contains two motor-power wires plus four encoder-related wires.
- Kept the first motor test scoped to motor power/control only.

### 2. Tools, Materials, and Software

Hardware: ESP32 DEVKIT_C, Hiwonder geared encoder motors, motor-driver hardware under evaluation, fuse/fuse holder, emergency-stop hardware, battery/power sources, jumper and power wires. Software: Arduino IDE and staged motor-test firmware.

### 3. Process Record - Key Operations / Parameters / Steps

- Separated motor power wires from encoder wires.
- Kept wheels off the ground for first power tests.
- Defined stop conditions for sparks, odor, heat, stalled buzzing, uncontrolled motion, or uncertain polarity.

### 4. Problems and Observed Phenomena

- The project had multiple possible power/protection approaches.
- Encoder wires made the motor harness more complex than a simple two-wire motor.
- Using an incorrectly rated protection device could create a false sense of safety.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Motor control, encoder measurement, and high-level navigation should not be introduced in the same first-power experiment.
- Protection must be in the real high-current path, not substituted by a regulator module.
- Common ground and power-domain separation had to be explicit.

**Attempts**
- Reduce the first powered test to one motor channel at a time.
- Keep encoder wires disconnected until motor polarity/direction is stable.
- Use clear stop conditions and record real observations instead of assuming success from compiled code.

**Final solution / decision:** Established a controlled pre-power checklist and separated the motor-power problem from later encoder and ROS2 work.

### 6. Test / Experimental Results

- Hardware roles were clearer.
- Unsafe shortcuts such as treating a regulator as a fuse were rejected.
- Project was ready for a tightly bounded Stage 4 motor bench test.

### 7. Remaining Issues

- Powered motor behavior still required a real Stage 4 bench test.
- Encoder integration and ROS2 control remained intentionally deferred.

### 8. Next Work Plan

- Run the first real driver/motor test and stop immediately if the physical system does not behave as expected.

---

## 19. 2026-07-28 - Atlas 6.0 Stage 4 - First Powered Motor Test Failure and Driver Redesign

**Recorder:** Eric  
**Phase:** Real Hardware Test / Failure Analysis / Architecture Change

### 1. Tasks and Completion

**Planned tasks**
- Validate ESP32 -> motor driver -> left/right motor control with wheels suspended.
- Confirm that software commands and serial communication translate into real motor movement.
- Collect physical evidence instead of declaring the stage successful from code output alone.

**Actual completed work**
- ESP32 firmware and serial command handling operated, but the expected motor movement did not occur in the initial driver path.
- Commands such as low and increased PWM were tested while the physical motor remained nonfunctional.
- Without a multimeter available in the moment, the system could not reliably separate power-path, ground, driver, or current-delivery causes.
- The Stage 4 architecture was redesigned around an L298N path with staged voltage/current measurement.

### 2. Tools, Materials, and Software

Software: dedicated safe motor-test firmware and Serial Monitor. Hardware: ESP32 DEVKIT_C, original driver test path, Hiwonder motors, power/protection hardware; L298N selected for the redesigned path.

### 3. Process Record - Key Operations / Parameters / Steps

- Observed the critical engineering distinction: firmware/serial success did not equal electromechanical success.
- Did not fabricate a motor-pass result.
- Redesigned the test plan to require measurement and single-motor validation before dual-motor operation.

### 4. Problems and Observed Phenomena

- The program accepted commands but the motor did not move.
- Cause could not be isolated without measuring the actual electrical nodes.
- Continuing to change code would not answer whether the fault was electrical.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Possible causes included power delivery, missing common ground, driver behavior, connection errors, insufficient current, or motor-driver incompatibility.
- A multimeter and staged isolation were more valuable than additional software changes.

**Attempts**
- Stop the failed driver path rather than repeatedly increasing PWM.
- Adopt L298N for a new Stage 4-R bench path.
- Lock a clear GPIO map and validate one motor, then the other, then both.

**Final solution / decision:** The failed first-power test became a documented architecture pivot. Atlas 6.0 moved to the L298N-based motor-control chain later used by the integrated release.

### 6. Test / Experimental Results

- Software and serial interface were confirmed independently of motor movement.
- The failure was preserved as project evidence.
- A higher-success Stage 4-R test architecture was established.

### 7. Remaining Issues

- L298N had not yet been fully accepted at the beginning of this record.
- Encoder integration still remained separate.

### 8. Next Work Plan

- Complete Stage 4-R with the L298N, lock motor GPIO, and validate physical direction/stop behavior before adding encoder feedback.

---

## 20. 2026-08-07 - Atlas 6.0 Stage 4-R / Stage 5 - L298N Drive Recovery, Direction Mapping, and Basic Movement

**Recorder:** Eric  
**Phase:** Motor Bring-Up / Direction Debugging / Safety Validation

### 1. Tasks and Completion

**Planned tasks**
- Establish a reliable L298N drive path and lock the final motor GPIO.
- Confirm left/right motor direction and STOP behavior before closed-loop work.
- Keep hardware wiring stable and correct direction errors in software where practical.

**Actual completed work**
- Locked the L298N motor-control map: left ENA13/IN1=14/IN2=4; right ENB33/IN3=32/IN4=23.
- A real TESTL 100 observation showed that the physical left wheel moved backward when commanded forward.
- Rather than rewiring the now-stable harness, the left motor direction was inverted in software while the right motor kept its physical polarity.
- The mobile-base control path progressed from non-movement into repeatable real motor operation.

### 2. Tools, Materials, and Software

Software: Stage 4-R motor firmware, early Stage 6/7 firmware family. Hardware: ESP32 DEVKIT_C, L298N, two Hiwonder geared encoder motors, suspended chassis, controlled motor-power source.

### 3. Process Record - Key Operations / Parameters / Steps

- Tested one physical motor at a time before dual-motor commands.
- Used software inversion to preserve wiring stability.
- Kept STOP/DISARM and bounded-duration movement as safety requirements.

### 4. Problems and Observed Phenomena

- One physical motor direction did not match the logical command.
- Low-PWM starts could buzz or fail to overcome static friction in later integrated tests.
- Changing physical wiring after encoder work began would create mapping risk.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Motor polarity and encoder polarity are separate engineering problems.
- DC motors may need extra starting torque even if a lower PWM is sufficient once already moving.
- A stable harness is valuable; direction can be normalized in software.

**Attempts**
- Invert the left motor in software.
- Preserve the right motor mapping.
- Later add a short startup-boost pulse rather than permanently raising cruise PWM.

**Final solution / decision:** Established the motor-direction abstraction that allowed higher layers to use logical FORWARD/BACK/LEFT/RIGHT without rewiring the physical drivetrain.

### 6. Test / Experimental Results

- L298N became the working motor-driver architecture.
- Basic motor direction and stopping behavior were reproducible.
- The drivetrain was ready for encoder calibration.

### 7. Remaining Issues

- Encoder channel mapping, sign, PPR, and physical distance calibration were still required.
- Closed-loop straight driving had not yet been tuned.

### 8. Next Work Plan

- Proceed to Stage 6 encoder mapping, sign learning, pulses-per-revolution measurement, and distance calibration.

---

## 21. 2026-08-08 - Atlas 6.0 Stage 6 - Dual Encoder Mapping and Calibration

**Recorder:** Eric  
**Phase:** Encoder Debugging / Calibration / Distance Control

### 1. Tasks and Completion

**Planned tasks**
- Identify which GPIO pair belongs to each physical wheel.
- Ensure forward encoder sign is correct rather than hiding errors with abs().
- Measure real wheel travel and pulses per revolution.
- Enable pulse- and distance-based stopping with independent wheel completion.

**Actual completed work**
- Locked physical right encoder to GPIO18/19 and physical left encoder to GPIO25/26.
- Added explicit forward-sign learning/check logic so the program verifies encoder direction after reboot.
- Final measured PPR values were LEFT=632.05 and RIGHT=634.17.
- Corrected the wheel calibration to a measured rolling circumference of 21.40 cm.
- Added target-pulse and target-distance commands, independent left/right stopping, stall timeout, total timeout, and spike protection.

### 2. Tools, Materials, and Software

Software: Atlas 6.0 Stage 6C V2/V3/V4 family. Hardware: ESP32 DEVKIT_C, L298N, dual Hiwonder encoder motors, suspended chassis, tape/ground reference for rolling circumference.

### 3. Process Record - Key Operations / Parameters / Steps

- Separated raw GPIO-group names from physical left/right meaning.
- Required short encoder-direction checks before allowing target-distance movement.
- Replaced an earlier incorrect wheel-travel assumption with the directly measured 21.40 cm rolling circumference.
- Used per-wheel PPR rather than a single shared nominal value.

### 4. Problems and Observed Phenomena

- Early encoder data could appear unstable or have unexpected sign.
- Raw channel names did not initially map cleanly to physical left/right labels.
- An early wheel-circumference value was not physically correct for final distance control.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Encoder sign errors must be fixed at the mapping layer, not hidden by absolute-value calculations.
- Left and right encoders had slightly different PPR and therefore required independent conversion.
- Real rolling circumference is more useful than relying on nominal wheel geometry.

**Attempts**
- Lock physical-to-GPIO mapping.
- Use forward-sign learning/check commands.
- Measure multiple revolutions and preserve independent PPR constants.
- Update distance conversion to the measured 21.40 cm rolling circumference.

**Final solution / decision:** Atlas 6.0 gained a trustworthy encoder foundation for later closed-loop motion: physical wheel identity, direction, PPR, and travel conversion were all explicit and testable.

### 6. Test / Experimental Results

- LEFT_PPR = 632.05.
- RIGHT_PPR = 634.17.
- Measured rolling circumference = 21.40 cm.
- Target-distance logic included 700 ms stall protection, bounded total runtime, and abnormal-pulse checks.

### 7. Remaining Issues

- Same-PWM open-loop driving still produced left/right progress mismatch.
- Distance stopping still needed better synchronization and endpoint behavior.

### 8. Next Work Plan

- Enter Stage 7 closed-loop straight synchronization and precision distance stopping.

---

## 22. 2026-08-12 and subsequent Stage 7 iterations - Atlas 6.0 Stage 7A-7D - Closed-Loop Straight Driving and Distance Accuracy

**Recorder:** Eric  
**Phase:** Control Tuning / Closed-Loop Motion / Iterative Test Optimization

### 1. Tasks and Completion

**Planned tasks**
- Quantify left/right mismatch under the same PWM.
- Add conservative synchronization without destabilizing already reliable low-speed operation.
- Build precise distance stopping while preserving STOP, stall, reverse-pulse, and timeout safety.
- Iterate based on real test data instead of theoretical motor symmetry.

**Actual completed work**
- Open-loop test f 80 1000 was repeated five times and remained stable.
- Average raw progress was approximately 928.6 pulses left vs 916.6 right; after independent-PPR normalization, the left side led by about 1.64%.
- SYNC V1 reduced average absolute left/right progress error to about 1.268% and reduced worst-case error from about 4.20% to 1.59%.
- V2 kept symmetric adaptive compensation rather than adding a fixed left/right bias because the leading wheel was not always the same in every run.
- FDS distance control evolved through multiple versions: dynamic braking, adaptive pulse approach, recovery cycles, dynamic cycle budgets, and continuous low-PWM control.
- Ground testing showed that PWM 80 could sustain movement, while very short stop/start pulses could fail to overcome static friction reliably; the later continuous-distance design therefore kept the motor at the lowest reliable continuous PWM and adjusted the lagging wheel modestly.

### 2. Tools, Materials, and Software

Software: Stage 7 Closed-Loop Straight V1/V2; Stage 7B Closed-Loop Distance V1-V5; Stage 7D Continuous Distance V6. Hardware: Atlas mobile base with L298N and dual encoders.

### 3. Process Record - Key Operations / Parameters / Steps

- Used normalized progress rather than raw pulse difference because the two encoders have different PPR.
- Updated compensation every 50 ms and bounded the extra PWM added to the lagging wheel.
- Introduced L298N dynamic braking for endpoint control.
- When long continuous motion overshot short targets, changed to pulse-approach control; when very short pulses became unreliable on the ground, moved again to continuous low-speed FDS with independent early braking.
- Adjusted cycle limits after real fds 15 tests required 86, 87, and 89 cycles, proving that a fixed budget could be too small for longer targets.

### 4. Problems and Observed Phenomena

- Open-loop left/right mismatch was real but variable.
- The first synchronized controller improved error but did not meet an arbitrary 30% improvement target.
- Continuous PWM caused significant overshoot for short targets.
- Pulse-by-pulse stopping improved endpoint control but could fail to restart the motors from rest on the ground.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Fixed bias was risky because the identity of the leading wheel could change between trials.
- Motor inertia and L298N braking behavior mattered near the endpoint.
- Static friction made extremely short low-PWM bursts unreliable even when the same PWM worked in continuous motion.

**Attempts**
- Use bounded adaptive compensation rather than permanent asymmetric PWM.
- Use braking and per-wheel completion.
- Base final control on measured motor startup/continuous behavior.
- Keep formal pass criteria separate from whether the safety logic completed successfully.

**Final solution / decision:** Established a data-driven closed-loop motion stack that was later carried into wireless and sensing stages without re-tuning the drivetrain every time.

### 6. Test / Experimental Results

- Open-loop five-run baseline recorded.
- SYNC V1 average absolute error approximately 1.268%; worst-case reduced to 1.59%.
- FDS pass criteria were explicit: final distance error <=10% per wheel and left/right final mismatch <=5%.
- Distance control retained stall, reverse-pulse, abnormal-pulse, STOP, and total-time protections.

### 7. Remaining Issues

- Long-range navigation was not the goal of 6.0; the controller was optimized for reliable tabletop/mobile-base experiments.
- Wireless communication still had to replace the dragging data cable.

### 8. Next Work Plan

- Add a Wi-Fi/TCP bridge without changing the proven motor/encoder/FDS behavior.

---

## 23. Mid-August 2026 - Atlas 6.0 Stage 7C - Wireless Bridge and Removal of the Driving Data Cable

**Recorder:** Eric  
**Phase:** Communication Integration / Safety Regression

### 1. Tasks and Completion

**Planned tasks**
- Remove the physical data cable from normal movement so cable drag no longer affects driving.
- Add Wi-Fi/TCP as a second command path while keeping the same processCommand() logic.
- Preserve Stage 7B drivetrain parameters and require heartbeat-based fail-safe stopping.

**Actual completed work**
- Created a Wi-Fi access point on the ESP32 and a TCP command server.
- USB Serial and Wi-Fi TCP were routed into the same command parser so wireless control did not fork the motor logic.
- Runtime reports were mirrored to USB serial and the active TCP client.
- Added a 350 ms TCP heartbeat timeout that forces STOP and DISARM when network control disappears.
- This architecture later evolved into the final ATLAS_6_0 AP / TCP control path used by the integrated release.

### 2. Tools, Materials, and Software

Software: Atlas_6_0_Stage_7C_Wireless_Bridge_V1.ino and later integrated firmware. Hardware: ESP32 Wi-Fi, L298N, dual encoders, mobile base, PC wireless connection.

### 3. Process Record - Key Operations / Parameters / Steps

- Explicitly froze drivetrain tuning before adding the network layer.
- Used one command parser for both USB and TCP.
- Added heartbeat safety before using wireless motion commands.
- Tested communication as its own layer rather than changing motor tuning at the same time.

### 4. Problems and Observed Phenomena

- A tethered USB/data cable physically affected free movement.
- A wireless command path creates a new failure mode: client disconnect or heartbeat loss.
- Network debugging can become confused with motor-control debugging if both are modified at once.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Wireless control is only acceptable when loss of communication becomes a stop condition.
- Duplicated command parsers could drift out of sync.
- The safest architecture is one low-level command/safety implementation with multiple transport inputs.

**Attempts**
- Keep motor/encoder code unchanged.
- Add TCP only at the transport boundary.
- Mirror status output and implement independent heartbeat timeout.

**Final solution / decision:** Atlas 6.0 became untethered at the command layer while retaining a deterministic ESP32 safety boundary. Communication loss was treated as a safety event, not a reason to keep moving on the last command.

### 6. Test / Experimental Results

- Wi-Fi/TCP command path worked.
- 350 ms heartbeat fail-safe was established and later retained in the final integrated firmware.
- Cable drag was removed from normal motion tests.

### 7. Remaining Issues

- The first Stage 7C AP credentials/port were development values and changed later in the integrated release.
- Distance sensing and autonomous obstacle behavior still had to be integrated.

### 8. Next Work Plan

- Integrate US-100 distance sensing as a physical veto layer before adding camera intelligence.

---

## 24. Mid-to-Late August 2026 - Atlas 6.0 Stage 8A-8B - US-100 Sensor Safety Gate and Suspended Integration

**Recorder:** Eric  
**Phase:** Distance Sensing / Safety-State Integration / Real Motor Validation

### 1. Tasks and Completion

**Planned tasks**
- Add the US-100 without weakening the already-proven encoder/motor safety logic.
- Make invalid or dangerously close distance data block forward motion.
- Validate sensor logic with motor output disabled before enabling real motor output.
- Require re-ARM after a safety event instead of automatically resuming motion.

**Actual completed work**
- Connected US-100 in Trigger/Echo mode using GPIO27 (Trig) and GPIO34 (Echo).
- Built Stage 8A with MOTOR_OUTPUTS_ENABLED=false so the entire safety state machine could be exercised without motor power.
- Used FORCE_STOP, CAUTION, CLEAR, STARTUP_STOP, and SENSOR_INVALID_STOP states with hysteresis.
- For compact no-motor tests, a temporary 25/40/45 cm threshold set was used; the formal Stage 8B real-motor logic restored the 25/50/55 cm policy.
- Created Stage 8B suspended integration with real motor output enabled only while wheels remained off the ground and power was controlled.

### 2. Tools, Materials, and Software

Software: Stage 8A Sensor Safety V1/V2 Compact; Stage 8B Suspended Integration V1. Hardware: ESP32, L298N, dual encoders, US-100, mobile base.

### 3. Process Record - Key Operations / Parameters / Steps

- First validated sensor states without allowing any motor output.
- Required several valid readings before treating the sensor as trustworthy.
- Applied hysteresis so the state did not oscillate around a threshold.
- After a STOP-class event, required a new ARM rather than silently continuing.

### 4. Problems and Observed Phenomena

- Distance thresholds suitable for a large test area were inconvenient for very small indoor bench spaces.
- An invalid sensor reading must not be interpreted as safe.
- Turning real motors on before logic validation would make sensor bugs physically dangerous.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Safety logic must fail closed.
- Hysteresis is needed near distance boundaries.
- Software-only and real-output variants should be separate acceptance steps.

**Attempts**
- Use a compact threshold set only for no-motor tests and explicitly restore formal thresholds for powered tests.
- Keep invalid data in a stop state.
- Enable real motors only after the no-output version passes.

**Final solution / decision:** Established US-100 as a physical veto authority: obstacle or invalid data can stop motion regardless of higher-level intent.

### 6. Test / Experimental Results

- US-100 became part of the low-level safety chain.
- Sensor safety could be validated independently of motor actuation.
- Suspended motor integration preserved the re-ARM requirement after unsafe states.

### 7. Remaining Issues

- Forward-only distance sensing was insufficient for rich left/right route selection.
- A scanning mechanism and camera-based perception were still needed for the planned autonomous behavior.

### 8. Next Work Plan

- Add servo-based scanning and an autonomous stop/backoff/scan/turn recovery state machine.

---

## 25. Late August 2026 - Atlas 6.0 Autonomous Obstacle Avoidance - Servo Scan, Startup Boost, and Recovery State Machine

**Recorder:** Eric  
**Phase:** Autonomous Behavior / Sensor Fusion Preparation / Motion Robustness

### 1. Tasks and Completion

**Planned tasks**
- Use US-100 scanning to select a safer direction after encountering an obstacle.
- Make low-speed starts reliable without permanently increasing cruise PWM.
- Create a bounded recovery sequence instead of a single open-loop turn command.
- Keep no-rear-sensor limitations explicit.

**Actual completed work**
- Added a scan servo and later standardized the continuous sweep sequence LEFT(5) -> CENTER(90) -> RIGHT(175) -> CENTER(90).
- Added a short startup boost (later integrated as PWM 220 for 150 ms) to overcome static friction before returning to normal cruise PWM.
- Implemented recovery behavior that stops first, performs a short bounded backoff, waits for safe sensor data, scans, then turns toward a safer direction.
- Developed integrated candidates through V3.x, including direction-map fixes and auto-recovery logic.

### 2. Tools, Materials, and Software

Software: integrated RC V3.x family including STARTUP_BOOST, DIRECTION_FIXED, and AUTO_RECOVERY variants. Hardware: ESP32, L298N, dual encoders, US-100, scan servo, mobile base.

### 3. Process Record - Key Operations / Parameters / Steps

- Kept startup boost short so it solved stall/static-friction behavior without turning into a new high-speed cruise setting.
- Made recovery stateful: STOP -> bounded reverse -> scan -> choose turn -> continue only when safe.
- Kept rear motion deliberately short because the robot had no rear obstacle sensor.

### 4. Problems and Observed Phenomena

- At low PWM the motors could buzz or fail to start from rest.
- Obstacle detection alone did not tell the robot which direction to choose.
- A recovery routine could become unsafe if reverse duration were unbounded.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Static friction requires more torque at startup than during continuous motion.
- US-100 can provide strong physical range evidence but only along the direction it is pointed.
- Without a rear sensor, reverse must remain tightly bounded.

**Attempts**
- Use a brief startup boost.
- Use servo scanning to collect directional range data.
- Use explicit recovery states and stop conditions instead of long blocking movement.

**Final solution / decision:** Atlas 6.0 moved from command-driven mobility to a real sensor-feedback behavior loop: detect -> stop -> recover -> scan -> turn -> continue.

### 6. Test / Experimental Results

- Low-speed startup became more reliable.
- Servo-based directional scanning was integrated.
- Auto recovery and US-100 veto behavior were incorporated into the integrated firmware family.

### 7. Remaining Issues

- Camera perception was still not reliable enough to become a safety authority.
- The initial image-scanning idea required its own dataset and validation process.

### 8. Next Work Plan

- Integrate the C950 as a PC-side perception sensor, first as a non-controlling baseline, then train models only if the heuristic scan is not reliable.

---

## 26. Late August 2026 - Atlas 6.0 Stage 12A - C950 Vision Baseline Failure, Dataset Collection, and AI Model Training

**Recorder:** Eric  
**Phase:** Computer Vision / Dataset Engineering / Model Iteration

### 1. Tasks and Completion

**Planned tasks**
- Use the external EMEET C950 to provide visual free-space / edge information without loading the ESP32.
- Begin with a non-controlling perception baseline.
- If hand-designed image thresholds are not reliable across scenes, collect labeled data and train models rather than continuously tuning arbitrary thresholds.

**Actual completed work**
- Built a 1280x720 / 30 FPS OpenCV baseline that estimated LEFT/CENTER/RIGHT connected tabletop/free-space from an adaptive appearance reference.
- Kept the first vision version completely disconnected from ESP32 and motor control so perception errors could not move the robot.
- Observed that the baseline scanning/data interpretation was not reliable enough across different scenes for final avoidance.
- Created labeled dataset collectors and split the problem into two tasks: directional traversability (FREE/BLOCKED) and global near-field edge safety (SAFE/EDGE).
- Collected multiple scene images, trained models, found remaining misclassifications, retrained, and repeated validation until release criteria could be met.

### 2. Tools, Materials, and Software

Software: Python, OpenCV, Ultralytics YOLO classification, dataset collectors, atlas_vision_stage12a1_camera1.py, edge ROI collector, directional/edge release scripts. Hardware: EMEET C950 connected to the PC; ESP32 and motors deliberately excluded from initial model validation.

### 3. Process Record - Key Operations / Parameters / Steps

- Used the lower/near-field part of the camera frame for edge-safety data so the model focused on the physically relevant tabletop boundary.
- Kept directional and cliff/edge decisions separate rather than training one overloaded class set.
- Saved raw/annotated frames and CSV/validation outputs.
- Used validation sets and explicit release scripts instead of accepting a visually impressive single test.

### 4. Problems and Observed Phenomena

- Heuristic scanning produced inaccurate or scene-dependent results.
- Early trained models still produced analysis errors in some conditions.
- Cropping/region selection could remove the very edge evidence needed for safety.
- A model can appear good in a demo while still making a dangerous BLOCKED->FREE or EDGE->SAFE error.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Color/appearance heuristics do not generalize reliably across lighting and tabletop conditions.
- Safety-critical edge perception needs a different objective from left/right free-space classification.
- Validation must prioritize dangerous false-safe errors, not only average accuracy.

**Attempts**
- Collect more representative scenes.
- Retrain when direct errors remain.
- Use tri-state outputs including UNKNOWN instead of forcing a confident answer.
- Require release-freeze checks with zero direct class swaps on the validation set at the selected threshold, while bounding the UNKNOWN ratio.

**Final solution / decision:** Replaced the unreliable single heuristic scanner with a structured perception pipeline built from data collection, model training, validation, retraining, and release-freeze gates.

### 6. Test / Experimental Results

- Created separate directional and edge-safety datasets/models.
- Built scripts that refuse to freeze a model when no acceptable threshold exists.
- Release logic explicitly treats UNKNOWN as a safe non-advance state rather than a guessed FREE state.

### 7. Remaining Issues

- Model validation still needed live integration with a real camera stream.
- The final navigation policy still needed to decide how much authority camera vs US-100 should have.

### 8. Next Work Plan

- Run live dual-model validation, then define a conservative fusion policy before the camera is allowed to influence navigation.

---

## 27. Late August 2026 - Atlas 6.0 Vision Release - Dual-Model Validation and Strict Edge-Safety Policy

**Recorder:** Eric  
**Phase:** Model Validation / Safety Policy / Live Camera Integration

### 1. Tasks and Completion

**Planned tasks**
- Freeze only models that pass validation gates.
- Validate the models live on C950 without immediately granting motor authority.
- Define a conservative policy that prioritizes cliff/edge safety over directional convenience.

**Actual completed work**
- Created release-freeze tooling for EDGE/SAFE and BLOCKED/FREE models.
- Release scripts searched confidence thresholds and rejected a model if no zero-direct-error tri-state threshold was available within the allowed UNKNOWN ratio.
- Built a live dual-model pipeline: evaluate the near-field EDGE/SAFE ROI first; only when globally SAFE is established does directional FREE/BLOCKED classification run.
- Added temporal smoothing / consecutive-frame confirmation for safe states.
- After real testing exposed remaining risk, the final master policy became stricter: a confident EDGE is immediate; weak/not-safe frames revoke SAFE permission; strong SAFE must persist across consecutive frames; LEFT/RIGHT camera authority is disabled for navigation and US-100 becomes the sole physical left/right authority.

### 2. Tools, Materials, and Software

Software: freeze_edge_roi_release.py, resolve_and_freeze_directional_release.py, atlas_live_dual_model_v1.py, atlas_vision_wifi_console_v3_EDGE_STRICT.py, later atlas_6_0_full_master_v1.py. Hardware: C950 on PC, ESP32 over Wi-Fi/TCP.

### 3. Process Record - Key Operations / Parameters / Steps

- Treated model freeze as a reproducibility step: selected model file, threshold, class mapping, validation counts, UNKNOWN behavior, and release config were recorded.
- Ran camera/model validation separately before full autonomous integration.
- Compared SAFE and EDGE diagnostic distributions and refused threshold-only fixes when class separation was insufficient.
- Made the final runtime policy more conservative than the raw model output.

### 4. Problems and Observed Phenomena

- A model that passes one validation can still be too permissive in live safety conditions.
- Directional camera outputs are less physically trustworthy than close-range US-100 measurements for left/right obstacle decisions.
- Edge safety needs fast reaction but SAFE permission should be harder to earn.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Classifier confidence is not itself a safety guarantee.
- Physical sensors and learned vision have different failure modes.
- A safety architecture should use each sensor where it is strongest rather than forcing symmetric authority.

**Attempts**
- Derive a stricter SAFE threshold from measured SAFE and EDGE diagnostics.
- Require multiple consecutive strong SAFE frames.
- Use camera primarily as strict edge/cliff safety while keeping US-100 as left/right physical authority.

**Final solution / decision:** Vision became a bounded safety subsystem rather than an unrestricted navigation brain. This was a major architecture correction: learned perception was used where it added value while physical range sensing retained final authority for directional obstacle avoidance.

### 6. Test / Experimental Results

- EDGE/SAFE and directional release candidates could be frozen only after explicit validation.
- Live dual-model validation pipeline was established.
- Final policy implemented fail-closed UNKNOWN behavior and strict SAFE confirmation.

### 7. Remaining Issues

- Full-system integration still needed the 5.0 expression/voice layer and the final ESP32 firmware.
- Camera processing remained PC-side.

### 8. Next Work Plan

- Reintegrate Atlas 5.0 body expression and voice with the 6.0 mobile/safety stack, then freeze the final integrated firmware.

---

## 28. Late August to Early September 2026 - Atlas 6.0 Final Hardware Integration - V3.5 / V3.5.2 Head Behavior Fix

**Recorder:** Eric  
**Phase:** Full Hardware Integration / Firmware Stabilization / Safety Regression

### 1. Tasks and Completion

**Planned tasks**
- Combine drivetrain, encoders, US-100 scanning, Wi-Fi/TCP watchdog, OLED, pan/tilt head, and RGB expression on one ESP32 without weakening the movement safety boundary.
- Restore the personality/body-expression capability from Atlas 5.0.
- Fix head behavior and keep the robot safe on boot, disconnect, and stale perception.

**Actual completed work**
- Integrated the final hardware map: L298N left ENA13/IN1=14/IN2=4; right ENB33/IN3=32/IN4=23; encoders left 25/26 and right 18/19; US-100 27/34; scan servo 21; OLED SDA16/SCL17; pan 5; tilt 22; RGB strip 15.
- Finalized boot state as DISARMED / AUTO OFF / US_ONLY / SWEEP ON.
- Finalized Wi-Fi AP control in the release line with ATLAS_6_0 and TCP port 8888.
- Retained the 350 ms network heartbeat timeout: communication loss forces STOP + DISARM.
- Required fresh camera SAFE for FUSION mode and treated stale/UNKNOWN center vision as STOP.
- Reintegrated OLED, RGB, and pan/tilt behavior and fixed head-profile behavior in V3.5.2.
- Kept pan/tilt electrically quiet until an explicit calibration/state action to reduce unnecessary motion.

### 2. Tools, Materials, and Software

Software: Atlas_6_0_Integrated_RC_V3, V3.2 STARTUP_BOOST, V3.3 DIRECTION_FIXED, V3.4 AUTO_RECOVERY, V3.5 FULL_HARDWARE_INTEGRATION, V3.5.1 RGB fix, V3.5.2 HEAD_BEHAVIOR_FIX. Hardware: complete Atlas 6.0 body.

### 3. Process Record - Key Operations / Parameters / Steps

- Integrated one subsystem at a time and kept earlier working versions as rollback points.
- Preserved reboot-safe behavior and STOP/DISARM semantics across all integration versions.
- Remapped the Atlas 5.0 expression hardware to GPIOs that did not conflict with the 6.0 drivetrain/sensors.
- Used explicit build banners/status output to identify which firmware was actually running.

### 4. Problems and Observed Phenomena

- Low-speed motor starts required startup boost.
- Physical motor direction mapping required a later correction in the integrated release line.
- Head motion could interfere with the robot if pan/tilt stayed actively driven without need.
- Adding many subsystems to one ESP32 increased the importance of a fixed GPIO map and fail-safe boot.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- The final robot needed a single authoritative hardware map.
- Expression features must never bypass motor safety.
- Communication and perception failures must transition to STOP/DISARM, not preserve the previous motion state.

**Attempts**
- Keep startup boost bounded.
- Lock final direction map in software.
- Detach/quiet head outputs when not required.
- Preserve explicit safety checks and mirrored status reporting.

**Final solution / decision:** V3.5.2 became the final Atlas 6.0 ESP32 integrated baseline, combining mobility, sensing, communication safety, and body expression without turning the expression layer into a motor-control dependency.

### 6. Test / Experimental Results

- Final firmware booted DISARMED.
- Heartbeat timeout and controlled network disconnect both stop/disarm.
- US-100 retained physical veto authority.
- FUSION required fresh camera-safe state.
- OLED/RGB/pan-tilt expression hardware was restored on the mobile robot.

### 7. Remaining Issues

- High-level PC-side voice/vision still needed a single master runtime.
- Final demo had to prove autonomous behavior, perception, and expression together.

### 8. Next Work Plan

- Run the final PC-side master program and demonstrate integrated autonomous behavior with conservative safety.

---

## 29. Late August to Early September 2026 - Atlas 6.0 Final Master Integration and Demo - Voice, Vision, Expression, Edge Safety, and Autonomous Tabletop Navigation

**Recorder:** Eric  
**Phase:** System Integration / Demo Validation / Version Closeout

### 1. Tasks and Completion

**Planned tasks**
- Combine C950 vision, ESP32 Wi-Fi/TCP, autonomous obstacle avoidance, strict edge safety, and Atlas 5.0 interaction/personality into one operational master program.
- Make human interaction safe even though keyboard input and TTS can block the main loop.
- Produce a real end-to-end demo that shows failures, retraining, fixes, and successful autonomous behavior.

**Actual completed work**
- Built atlas_6_0_full_master_v1.py using one shared C950 instance, Wi-Fi/TCP ESP32 control, strict edge-safety calibration, local TTS, and optional English/Chinese voice input.
- Re-entered FUSION mode in a DISARMED state; AUTO still required explicit user authorization.
- Implemented a safety-first typed-dialogue path that sends AUTO OFF -> STOP -> DISARM before blocking for keyboard/TTS interaction.
- Retained the final perception policy: edge model provides strict cliff/edge permission; US-100 is the sole left/right physical authority for navigation.
- Completed the development sequence captured in the final demo: define the goal; write US-100 obstacle-avoidance logic; repeatedly tune parameters; achieve ultrasonic-only avoidance; add the C950; discover the initial scan system was inaccurate; collect multi-scene data; train and retrain AI models; validate release criteria; fix residual real-test errors; and finally complete successful integrated testing.

### 2. Tools, Materials, and Software

Software: atlas_6_0_full_master_v1.py, atlas_6_0_brain_integration_v1.py, strict-edge vision console, model-release configs, V3.5.2 ESP32 firmware. Hardware: complete Atlas 6.0 mobile robot, EMEET C950 on the PC side, ESP32 Wi-Fi AP/TCP, L298N, encoders, US-100, scan servo, OLED, pan/tilt, RGB.

### 3. Process Record - Key Operations / Parameters / Steps

- Checked release files and edge-safety diagnostic separation before entering live control.
- Opened the camera once and shared that stream across the master program instead of competing camera processes.
- Connected ESP32 over TCP and kept periodic heartbeat/status traffic.
- Kept controller DISARMED until explicit ARM.
- Converted voice/text interaction into an explicit safe-stop event before performing blocking user interaction.

### 4. Problems and Observed Phenomena

- Initial camera scanning was not accurate enough to trust.
- Model training required several iterations and re-validation.
- Human interaction could starve heartbeat/control if the robot stayed moving while the program waited for input or TTS.
- Combining personality with autonomy risked turning expressive behavior into a safety distraction.

### 5. Root-Cause Analysis and Corrective Actions

**Likely causes / engineering interpretation**
- Perception quality must be proven through data and validation, not appearance in one demo.
- Blocking UI/audio work cannot safely coexist with active motion unless motion is stopped first.
- Robot personality should be layered above, not below, the safety state machine.

**Attempts**
- Use release-gated models and a strict runtime policy.
- Always stop/disarm before blocking interaction.
- Keep physical range sensing in the low-level safety loop.
- Treat expression/voice as optional higher-level behaviors that cannot bypass STOP/DISARM.

**Final solution / decision:** Atlas 6.0 closed as a mobile hardware robot that combined real motor control, encoder feedback, closed-loop motion, ultrasonic obstacle sensing, Wi-Fi/TCP safety, PC-side AI vision, autonomous recovery, and the personality/expression lineage from Atlas 5.0.

### 6. Test / Experimental Results

- Autonomous obstacle avoidance succeeded after iterative US-100 tuning.
- C950 vision progressed from an unreliable baseline to release-gated AI safety models.
- Wireless control removed the driving data cable.
- Final integrated firmware and master program supported safe edge-aware autonomous tabletop behavior and Atlas-style expression.
- The final demo documented both failure/retraining loops and the successful result rather than presenting only the finished system.

### 7. Remaining Issues

- Atlas 6.0 did not implement full SLAM/Nav2 mapping; that work was intentionally moved to Atlas 7.0.
- Camera compute remained on the PC.
- Final mobile power and embedded compute architecture would continue to evolve in 7.0.

### 8. Next Work Plan

- Freeze Atlas 6.0 source code, models, logs, and demo evidence.
- Use 6.0 as the proven real-time/safety base for Atlas 7.0 ROS2 mapping and navigation.

---

## Appendix A - Atlas 6.0 Final Technical Baseline

### Final ESP32 / Hardware Map

| Function | Final Atlas 6.0 Mapping |
|---|---|
| Left motor L298N | ENA GPIO13; IN1 GPIO14; IN2 GPIO4 |
| Right motor L298N | ENB GPIO33; IN3 GPIO32; IN4 GPIO23 |
| Left encoder | GPIO25 / GPIO26 |
| Right encoder | GPIO18 / GPIO19 |
| US-100 | TRIG GPIO27; ECHO GPIO34; 3.3 V logic supply in final firmware notes |
| Scan servo | GPIO21 |
| OLED | SDA GPIO16; SCL GPIO17 |
| Head pan | GPIO5 |
| Head tilt | GPIO22 |
| RGB strip | GPIO15 |
| Final Wi-Fi AP | SSID ATLAS_6_0 |
| Final TCP port | 8888 |
| Network heartbeat fail-safe | 350 ms -> STOP + DISARM |

### Key Measured / Tuned Values

- Left encoder: **632.05 pulses/revolution**.
- Right encoder: **634.17 pulses/revolution**.
- Measured rolling wheel circumference: **21.40 cm** (confirmed 2026-08-08).
- Stage 7 open-loop baseline at PWM 80 / 1000 ms: five stable trials; left average 928.6 pulses, right average 916.6 pulses; normalized left lead about 1.64%.
- Stage 7 SYNC V1: average absolute error about 1.268%; worst error reduced from about 4.20% to 1.59%.
- Final integrated startup boost: PWM 220 for 150 ms before returning to cruise PWM.
- Final integrated scan sequence: LEFT 5 deg -> CENTER 90 deg -> RIGHT 175 deg -> CENTER 90 deg.
- Final integrated safety state: reboot DISARMED; network timeout/disconnect STOP + DISARM; FUSION requires fresh camera SAFE; US-100 retains physical veto authority.

## Appendix B - Principal Atlas 6.0 Source/Evidence Files

- `Atlas_6.0 plan document and Atlas_Master_Context_1.0-6.0.md`
- docs/09_ENGINEERING_LOG.md and Stage 4-R engineering plan/manual
- Atlas_6_0_Stage_6C_V3/V4.ino
- Atlas_6_0_Stage_7_Closed_Loop_Straight_V1/V2.ino
- `Atlas_6_0_Stage_7B_Closed_Loop_Distance_V1-V5.ino`
- `Atlas_6_0_Stage_7C_Wireless_Bridge_V1.ino`
- `Atlas_6_0_Stage_7D_Continuous_Distance_V6.ino`
- Atlas_6_0_Stage_8A_Sensor_Safety_V1/V2_Compact.ino
- `Atlas_6_0_Stage_8B_Suspended_Integration_V1.ino`
- `atlas_vision_stage12a1_camera1.py and dataset collectors`
- `freeze_edge_roi_release.py, freeze_directional_release.py, resolve_and_freeze_directional_release.py`
- `atlas_live_dual_model_v1.py and strict-edge vision console`
- `Atlas_6_0_Integrated_RC_V3 through V3.5.2_HEAD_BEHAVIOR_FIX.ino`
- `atlas_6_0_brain_integration_v1.py`
- `atlas_6_0_full_master_v1.py`
- Archived project/chat records and demo-development notes

## Appendix C - Version Transition

Atlas 6.0 intentionally stopped short of full SLAM/Nav2 mapping. Its main contribution was a proven real-time mobile-robot base: motor control, encoder feedback, closed-loop distance behavior, ultrasonic safety, Wi-Fi/TCP fail-safe communication, PC-side vision, autonomous obstacle recovery, and reintegrated Atlas personality/expression. Atlas 7.0 can therefore focus on mapping, localization, sensor fusion, and navigation rather than rebuilding these lower-level capabilities from zero.
