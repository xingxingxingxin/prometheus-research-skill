# Ralph Loop Task Execution Template

> This template is used for tasks executed in Ralph Loop mode.
> Variables are denoted as {{variable_name}}.

---

## Current Task

- **Task ID**: {{task_id}}
- **Phase**: {{phase}}
- **Description**: {{task_desc}}
- **Iteration**: {{iteration}} / {{max_iterations}}

---

## Your Mission

You are in **Ralph Loop** mode - an iterative execution environment where you can refine your work across multiple attempts.

### How Ralph Loop Works

1. **Same Task, Multiple Attempts**: Each iteration you see this same prompt
2. **Work Persists**: Your previous work is saved in project files and git history
3. **Build Incrementally**: Review what was tried before, then improve
4. **Signal Completion**: When truly done, output the completion promise

---

## Current State

### Project Context
{{project_context}}

### Previous Attempts Summary
{{previous_attempts}}

### Files Modified So Far
{{files_modified}}

---

## Instructions

### Step 1: Review Previous Work
```bash
# Check recent git commits
git log --oneline -5

# Check recently modified files
git status

# Review any logs or notes
cat Logs/operational.log | tail -20
```

### Step 2: Continue Task Execution
Based on previous attempts:
- **If first iteration**: Start fresh on the task
- **If errors occurred**: Debug and fix the issues
- **If partial progress**: Continue from where you left off
- **If blocked**: Try an alternative approach

### Step 3: Validate Progress
Run tests or validation to verify your work:
```bash
# Run relevant tests
pytest tests/ -v --tb=short

# Validate code quality
flake8 src/

# Check if the task requirements are met
# (varies by task type)
```

### Step 4: Document Progress
Update relevant logs and notes:
```bash
# Log your progress
echo "[$(date)] Iteration {{iteration}}: [brief summary]" >> Logs/ralph_progress.log
```

---

## Completion Criteria

{{completion_criteria}}

---

## How to Signal Completion

When **ALL** of the following are true:
1. Task is fully implemented/complete
2. Tests/validation pass
3. Code is committed to git
4. Documentation is updated

Output the completion promise:

```
<promise>{{completion_promise}}</promise>
```

**Important**: Only output this when the task is genuinely complete!

---

## If Blocked

If you cannot complete the task after multiple attempts:

1. Document the blocker clearly
2. Create a help request:
   ```markdown
   # Help Request

   ## Task: {{task_id}}
   ## Blocker: [describe the issue]
   ## Attempts: [what you tried]
   ## Suggested: [what might help]
   ```
3. Save to `Communication/outbox/help_request_{{task_id}}.md`
4. Output: `<promise type="blocked">NEEDS_HELP</promise>`

---

## Important Reminders

- **Don't repeat failed approaches** - check git history first
- **Make progress each iteration** - don't just try the same thing
- **Document your work** - future iterations need context
- **Test before claiming done** - verification is required
- **Ask for help when stuck** - don't spin forever

---

## Task-Specific Context

{{task_specific_context}}

---

*Begin iteration {{iteration}} of {{max_iterations}}*
