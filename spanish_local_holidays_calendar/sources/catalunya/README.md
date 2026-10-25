# Catalunya source

Fetches holidays for Catalan municipalities from the Generalitat's
official open-data portal (analisi.transparenciacatalunya.cat), queried
as JSON -- a different shape entirely from the Balearics' source (see
[`../illes_balears/README.md`](../illes_balears/README.md)), which
scrapes HTML.

It has no holiday *name* field at all:

- Regional holidays are named via a lookup of Catalonia's known fixed
  dates (the two Easter-relative ones computed from Easter Sunday, since
  they move every year).
- Local holidays are always given a generic translated name ("Festa
  local"/"Fiesta local") since the source's own "festiu" text field
  turned out to contain leftover test/junk entries and isn't trustworthy
  as a display name.
