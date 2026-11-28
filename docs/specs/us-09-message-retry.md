# US-09: Retry a failed message

As a customer, I can retry the same message and attachment without typing them again or creating duplicate saved work.

## Acceptance
- A failed or interrupted response ends loading and offers a simple retry action.
- Retry preserves the exact original text, attachment and request identity.
- The server saves each message and attachment once, including after a lost response or concurrent duplicate request.
- After recovery, the page shows the canonical saved conversation and allows the next valid action.

## Implementation preparation
Inspection found that App.retry sends the last text with a null attachment, post_message unconditionally inserts a message and writes a new upload, and sendMessage treats stream EOF without a done/error event as success.

Use a stable client operation ID per new message. Reuse it for every retry, with the original text/file/language held in memory. Persist the operation on the server, bound to its conversation and payload. Reject reuse with a different payload. Serialize concurrent operations for a conversation and prevent later messages from bypassing unfinished work. A completed retry returns saved results without another model call. An interrupted operation resumes its existing graph checkpoint rather than appending its user message again. Recover database writes separately from graph completion, so a completed checkpoint cannot lose or duplicate the saved assistant reply. Avoid holding a request transaction open across SSE yields.

The stream client must require a terminal event and clear loading on every failure path. Retry replaces the failed optimistic turn instead of appending another copy. Reload the canonical saved conversation after successful recovery. Retaining a File in memory supports retries on the current page; saved-claim restoration across reload is story 10.

## Required verification
- Failure before upload, after user-message save, during graph execution, and after graph completion but before database commit.
- Lost terminal response and repeated completed retries.
- Concurrent identical retries and conflicting payload reuse.
- One saved user message, one attachment/file, and one assistant answer after recovery.
- Original file/text retained, partial stream diagnosed, loading cleared, and subsequent progress enabled in the frontend.

Frontend implementation retains operation IDs and files, detects interrupted streams, and reloads canonical state. The server now persists operation identities and responses, rejects changed retry payloads, serializes graph execution with a session advisory lock, and resumes checkpoints. Completed retries and failed response-save recovery pass API tests. Concurrent retries, interruptions during graph execution, service recovery, stream cancellation and claim-action conflicts are now covered by passing backend tests. Claim actions share the conversation reservation lock and reject pending message operations. Frontend editing and new messages are blocked until the failed message is recovered. The browser test drops the terminal response after a file upload, retries successfully, verifies one saved user message, and completes submission, review and history reload. Full backend suite: 130 passed; frontend: 47 passed; type check, build, lint and formatting passed.
