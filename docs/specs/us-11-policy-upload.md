# US-11: Upload and identify a policy

Customers can upload a policy PDF separately from claim evidence. The policy panel shows the saved filename, upload/checking progress, errors and the current source of coverage wording.

Supported files are unencrypted, structurally readable PDFs with 1–300 pages, a .pdf filename and PDF MIME type, within MAX_UPLOAD_MB (10 MB by default). Text extraction and readability for searching are story 12. A scanned but structurally valid PDF may upload here; it is never marked ready for searching.

PolicyDocument records are separate from Attachment evidence. Uploads neither add chat messages nor set photo evidence. Storage paths are private server details and are omitted from responses. The selected file survives refresh. Repeating identical bytes returns the existing document; replacing another policy is story 14. New uploads require a pre-submission claim and no unfinished message. Existing access rules protect both read and upload endpoints.

The initial status is “Uploaded; awaiting text preparation”. Coverage source remains standard GDV AKB 2015 demo wording, clearly stated before and after upload. Policy search preparation and use are stories 12 and 13. This story does not claim uploaded wording is already searched.

Verification covers PDF type/structure/encryption/size validation, conversation scoping, filename sanitization, idempotency, separation from evidence, saved metadata, retryable UI errors, locked claims and browser restoration. Public demo copy asks for sample policies.
