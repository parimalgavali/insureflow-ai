# US-10: Continue the current claim after refresh

As a customer, I can return to my saved conversation, claim summary and status after refreshing the page.

- Persist only the current conversation ID, with graceful handling when browser storage is unavailable.
- Fetch saved state through the existing authenticated conversation endpoint. Do not silently create a new conversation when restoration fails.
- Explain missing/inaccessible conversations and offer Retry, optional in-memory access credentials, and Start new claim.
- Start new claim creates another conversation; it does not alter or delete the old saved claim. Update the browser's current ID only after successful creation.
- Store no credentials in browser storage. Discard the legacy stored demo token; keep new credentials in memory and request them again after reload.
- Respect restored status: customers may chat while collecting details or replying to a reviewer, but cannot chat after assessment/submission/review.
- Recover pending message operations after reload using their saved server input and file. Do not require an attachment that was only held in the old page's memory.

Implementation checkpoint: current-ID persistence, restore/error/new-claim UI, in-memory credentials and status restoration are implemented. Pending-message recovery across refresh, browser verification, and final review remain before publishing.
