# Illes Balears source

Scrapes the CAIB (Govern de les Illes Balears) labor calendar page's HTML
-- a different shape entirely from Catalunya's source (see
[`../catalunya/README.md`](../catalunya/README.md)), which queries a
JSON API instead.

Discovers every municipality listed on the page as a single entry (no
sub-localities) -- 48 of the Balearics' 67 municipalities, Palma among
them -- plus the individual sub-localities of municipalities split into
several of them (e.g. Andratx / Port d'Andratx / s'Arracó), fetchable by
sub-locality name just like any other municipality. CAIB consistently
lines up a split municipality's data cell as one shared holiday followed
by one sub-locality-specific holiday, repeated per sub-locality in the
same order as the heading names -- but where a row doesn't fit that
shape (Sant Josep de sa Talaia groups several place names under each
heading entry instead of listing them one-by-one), the pairing would be
a guess, so it's skipped rather than risking a misattributed holiday.

The source also doesn't separate national from regional holidays -- its
"general Illes Balears" list already folds Spain's national holidays
(New Year, National Day, Christmas, etc.) in with the Balearics' own
additions (e.g. Dia de les Illes Balears). It's tagged `scope: regional`
as a whole rather than guessing a split; local holidays are tagged
`scope: local`.
