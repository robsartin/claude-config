---
name: week-dates
description: Use when the user wants the week's agenda filled in from their calendar — "fill my week", "populate the calendar agenda", "put my calendar in This Week", or right after Archive Weekly resets the Obsidian weekly note.
---

# Week Dates

Fills the **Google Calendar Agenda** section of `This Week.md` from Google Calendar.
The note lives in the planning dir that
`python3 "${CLAUDE_PLUGIN_ROOT}/bin/morning_brief.py" paths` prints.

**REQUIRED BACKGROUND:** read `${CLAUDE_PLUGIN_ROOT}/skills/month-dates/SKILL.md`. Its
rules for items, times, locations, one item per appointment, which events are left
out, and the ground rules apply here unchanged. This skill only says what differs.

## 1. Check the note is this week's

Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/morning_brief.py" week`. It prints the current
week's label (`week`) and its first and last day (`start`, a Sunday; `end`, a
Saturday). Never work the label out by hand: the vault's weeks are not ISO weeks.

Compare `week` with the note's frontmatter `week:`.

- **Same label:** continue.
- **Different or missing:** write nothing. Tell the user the note is still the one for
  `<week>` and that Archive Weekly has to run first. Stop.

## 2. Read the calendar

Primary calendar only, from `start` 00:00 to the day after `end` 00:00, ordered by
start time. The whole week is read, days already past included.

## 3. Write the section

Replace everything between the `# 🗓️ Google Calendar Agenda` heading and the next `# `
heading. Touch nothing else in the note.

The section is always these six lines, in this order:

```markdown
- **Mon:** Ray 10am; FDA update 6; Apollo 1 documentary 7
- **Tue:** 
- **Wed:** Shave 12:15; massage 2
- **Thu:** Dr. Lee 3:30
- **Fri:** Drive to wedding
- **Sat/Sun:** Sun: Church 10:55am; sangha 11:30am / Sat: Megan's wedding 1:45
```

- **Labels:** exactly as shown, with no dates.
- **A day with no events:** its label with nothing after it.
- **Sat/Sun:** the week's Sunday (`start`) first, then its Saturday (`end`), each
  introduced by `Sun:` or `Sat:` and joined by ` / `. A half with no events is omitted
  along with its ` / `.
- **Items:** month-dates' item recipe. Nothing else goes on a line: no notes about
  overlaps, no meeting platform, no closing full stop.

## 4. Report

In chat, not in the note: the week label and date range written, each event left out
and which exception applied, and any same-day events whose times overlap.
