# Community Source Audit

This document records whether candidate community sources appear suitable for direct collection in the current MVP.

## Summary

- `DCInside`: keep disabled by default
- `Clien`: keep disabled by default
- `FM Korea`: keep disabled by default
- `Mock/local demo sources`: allowed for development

## Why These Sources Stay Disabled

### DCInside

Observations:

- `https://www.dcinside.com/robots.txt` currently includes `User-agent: * Disallow: /`
- no official public post collection API was confirmed from official source material during this audit
- requested candidate boards:
  - `https://gall.dcinside.com/mgallery/board/lists/?id=krstock`
  - `https://gall.dcinside.com/mgallery/board/lists?id=stockus`

Implication:

- automated crawling should remain disabled unless a clearly permitted access path is documented and reviewed
- both requested boards are registered in this repository as disabled source metadata only

### Clien

Observations:

- direct fetch attempts for `https://www.clien.net/robots.txt` were denied by robots handling during audit
- no official public post API was confirmed from official source material during this audit

Implication:

- keep as disabled connector unless an official API or clearly allowed public feed is identified

### FM Korea

Observations:

- public post pages are discoverable on the web, but no official public posts API was confirmed from official source material during this audit
- this is not enough, by itself, to justify enabling automated collection

Implication:

- keep as disabled connector pending formal source-policy review

## Allowed Development Pattern

For development and UI work:

- use mock connectors
- use local static HTML fixtures
- use RSS or official APIs where available

This repository currently follows that pattern for both market and politics community experiences.

## Review Checklist Before Enabling Any Community Source

1. Confirm `robots.txt` permits the intended fetch path.
2. Confirm terms of service allow automated collection for this use case.
3. Confirm rate limits and identification requirements.
4. Minimize personal data retention.
5. Hash or omit author identifiers where possible.
6. Document source-specific constraints in the connector.
