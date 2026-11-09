## Fetch and chunk article content

Title/description only gets you so far - the actual article body lives at
`article_url` on the publisher's site. This step fetches each URL, uses
`trafilatura` to extract just the article text (stripping nav/ads/related
links/etc.), and splits it into overlapping chunks so each chunk can be
embedded and retrieved independently. Any URL that fails to fetch/extract
(paywall, timeout, dead link) is skipped rather than failing the whole job.
