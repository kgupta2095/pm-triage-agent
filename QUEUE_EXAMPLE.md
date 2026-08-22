# Triage queue (example output, mock mode)

Mode: mock. Every item starts as Status: PENDING. Review each spec,
change Status to APPROVED (or REJECTED), then run:
`python run.py --post --repo owner/name --yes`

## 1. [BUG] Hi team, the export button on the reports page

Priority: high  
Status: PENDING

### Problem
Hi team, the export button on the reports page fails with a 500 error whenever I pick a date range longer than 3 months. Worked fine last month. We need these exports for a board meeting Friday.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 2. [FEATURE] Would be great if we could get Slack notifications

Priority: medium  
Status: PENDING

### Problem
Would be great if we could get Slack notifications when a client uploads a document, right now we only find out when we happen to log in. A daily digest would also work if realtime is hard.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 3. [BAU] Can someone rename the "Archived" tab to "Inactive"? Two

Priority: low  
Status: PENDING

### Problem
Can someone rename the "Archived" tab to "Inactive"? Two customers have told us they thought archived meant deleted. Just a label change as far as I can tell.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 4. [BUG] The mobile app shows the wrong timezone for shift

Priority: high  
Status: PENDING

### Problem
The mobile app shows the wrong timezone for shift start times for anyone outside the head office region. A carer in Perth saw 11am for a shift that is actually 8am local. This is causing missed visits.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 5. [FEATURE] We keep getting asked for a way to bulk-assign

Priority: medium  
Status: PENDING

### Problem
We keep getting asked for a way to bulk-assign clients to a coordinator when someone goes on leave. Today it is one at a time and takes an hour for big caseloads.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 6. [BAU] Please add support for read-only permissions on invoices for

Priority: low  
Status: PENDING

### Problem
Please add support for read-only permissions on invoices for the finance assistant role. They currently either see nothing or can edit everything, and the workaround is screenshots.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 7. [BUG] Search is broken for names with apostrophes. Searching O'Brien

Priority: high  
Status: PENDING

### Problem
Search is broken for names with apostrophes. Searching O'Brien returns nothing but Obrien returns the client. Customers with Irish names are effectively unsearchable.

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?

## 8. [BAU] Small one: the colour of the "overdue" badge is

Priority: low  
Status: PENDING

### Problem
Small one: the colour of the "overdue" badge is nearly the same red as "urgent". Support keeps mixing them up on calls. Could we change one of them?

### Proposed scope
- Reproduce or validate the request against current behaviour
- Smallest change that resolves the stated problem
- Out of scope: adjacent redesigns

### Acceptance criteria
- [ ] The behaviour described above is resolved or delivered
- [ ] No regression in the surrounding flow
- [ ] Copy and edge cases reviewed

### Open questions
- Which users or accounts are affected, and how many?
- Is there a workaround today?
