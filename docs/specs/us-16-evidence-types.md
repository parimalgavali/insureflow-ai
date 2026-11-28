# US-16: Identify claim attachments correctly

Customers choose the attachment purpose: damage photo, repair estimate, police report or other document. The server checks the actual format separately. A PDF can be a report or estimate; it cannot be a damage photo. A picture of a report can be labelled as a document without setting Photos attached. The selected purpose is a customer label, not a claim that the contents have been understood or independently verified.

JPEG, PNG and WebP images must have matching MIME type, extension, signature and decodable contents. Images are limited to one frame, 20 million pixels and 20,000 pixels per dimension. PDFs must have a matching extension/signature, be readable and unencrypted, and contain 1–300 pages. All files retain the configured MAX_UPLOAD_MB limit (10 MB by default). Names are reduced to a basename and limited to 200 UTF-8 bytes, leaving room for the private storage prefix; control characters are rejected. Invalid files fail before saving a message, operation or attachment.

Content checks run in a separate worker with a 15-second timeout, CPU limit and memory limit where supported. This is bounded parsing, not a full operating-system sandbox or malware scanner. No public attachment download endpoint is added.

Each customer/reviewer claim response includes only that conversation's attachment metadata, never its storage path. The claim screen shows name, purpose, actual format and processing state, including after reload and a failed assessment. New files say Uploaded, not yet analysed for claim details. Older uploads remain Not verified; migration 0010 does not guess their type or rewrite previously saved facts.

Only a newly verified image labelled damage photo automatically sets Photos attached. The extractor cannot infer this fact from a filename, PDF or attachment count. The per-turn signal is consumed so a later turn cannot override a manual correction. Explicit customer/reviewer fact corrections remain supported.

Message retries retain the original purpose alongside the file, text and operation ID. A rejected upload restores the draft and prior claim state so the customer can change or remove the file. Network and assessment failures continue to use the existing saved-operation retry flow. Uploaded bytes are stored once and replayed without duplicate files.

Verification covers real JPEG/PNG/WebP decoding, PDF/photo separation even when extraction guesses otherwise, document-purpose image uploads, corrupt/spoofed/animated files, long filenames, upload limits, safe metadata, legacy flags, draft restoration, stable retries and customer/reviewer attachment display. The recorded browser flow uses a real PDF and exercises a lost response followed by retry. PDF content suggestions and confirmation are separate stories #74 and #75.

Image parsing follows the official [Pillow Image API](https://pillow.readthedocs.io/en/latest/reference/Image.html) and [security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html): restrict formats, check dimensions, verify, reopen and decode.

Local validation: 171 backend tests and 71 frontend tests passed, along with lint, formatting, type checking, the production build and the full recorded browser flow. The browser flow covers rejecting a broken image, restoring its draft, replacing it with a real PDF, keeping both uploaded PDF types after reload, and retrying a lost response without duplicate files.
