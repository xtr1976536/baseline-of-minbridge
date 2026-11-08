# Security policy

Do not report suspected credentials in a public issue or paste them into logs.
Revoke the credential first, then contact the maintainers through the private
channel associated with the eventual public repository.

API keys belong in a local `.env` file or a secret manager. The repository's
public-release scan is a guardrail, not a substitute for provider-side rotation
or a dedicated secret scanner. Historical exposure must be handled as compromise
even when the value no longer appears in the current tree.
