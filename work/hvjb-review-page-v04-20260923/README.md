# HVJB whole-line review page v04 — 2026-09-23

One local entry point for the six reviewed diagrams, the 119-second concept video,
20 jobs, and 92 saved-model features. It uses plain HTML/CSS/JavaScript and local
files; there are no external scripts, network data requests or autoplay.

The page connects existing records. It does not select a robot, a tool, a hidden
connection or a physical assembly method. Source geometry and the v03 motion bank
are unchanged. The 92 photo features are not a complete physical BOM.

## Construction and readback

`build_page.py` requires a new output directory. It preserves the 26 previously
delivered document files, includes one process-review MP4, and checks the hashes
of the video, atlas and original product photograph while copying them.

The first build stopped because the historical 2026-09-13 Downloads photograph
path no longer existed. The source was changed to the existing connection-map
package copy, with the same recorded SHA-256
`5724681b4bef4399f0799751a62577e48ef9b7fd3d6ed5b56d85fd95924937ad`.
The incomplete staging directory was retained. No model or measurement changed.

`verify_page.py` reads every delivery hash, local asset link, embedded record and
bidirectional job/feature association. It also checks the complete scene timeline
and the inherited document/video/atlas identities. These are packaging checks,
not physical acceptance criteria.

Browser UI inspection was attempted using the available CUA tool. Both `iab` and
`chrome` returned `Browser is not available`; the inventory was
`{"apps":[],"browsers":[]}`. Interactive behavior and responsive layout have
therefore not been observed in an actual browser in this session. JavaScript
syntax and static references were checked separately. The PDF, PNGs and MP4 remain
directly accessible without the page.

## Delivery

`deliver_page.py` appends missing files to the already delivered v04 folder only
after reading back every existing document file. It refuses changed existing
paths. The original document manifest and files remain unchanged. The page has
its own `review_manifest.json`, `page_qa_receipt.json` and append receipt.

