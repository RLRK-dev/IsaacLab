# OP030 B stagger v06 integration observations

Observed: 2026-09-10T22:36:03.930225+09:00. Native SHA256 `8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338`.

Prepared timeline: 14,062 frames / 468.7 s. Frozen A/C and final B saved poses match the prepared tracks with the station Y offset applied once.

| Scope | Saved evidence |
|---|---|
| entry transfer | 346 frames; payload and fixture hits 0 |
| a_b transfer | 271 frames; payload and fixture hits 0 |
| b_c transfer / drawer return | 271 frames; payload and fixture hits 0 |
| Concurrent C prefill | 264 frames; moving pairs 0; 6 fixed pairs recorded separately |
| Initial B drawer presentation | 76 frames; hits 0 |
| b_initial against A | 7,165 frames; hits 0 |
| b_final against C | 2,167 frames; hits 0 |
| c_loaded against A | 6,902 frames; hits 0 |
| c_loaded against B | 3,787 frames; hits 0 |
| A against fixed background | 7,165 frames; unexpected pairs 0; 1 original floor pairs separate |
| B against fixed background | 3,787 frames; unexpected pairs 0; 1 original floor pairs separate |
| C against fixed background | 2,430 frames; unexpected pairs 0; 1 original floor pairs separate |

Native readback covers B poses, retained A/C poses, proper rotation, world −X drawer travel, ten presented UIDs and eight returned stock UIDs. Existing full-bank A/C clearance against the relocated four-part pipe is reused with its original observation timestamps.

Original fixed floor/base and stationary pipe/bracket contacts remain separately recorded with raw report digests. No new contact acceptance exception.

Saved-frame matrix and FCL/AABB geometry observations only. No continuous-time collision guarantee, force, fastening quality, hardware safety or formal physical-validity verdict. Fixture checks retain their explicitly recorded within-mechanism omissions.

All source digests, exact intervals, fixed-pair records and scope limits: `audit/op030_stagger_v06_integration_evidence.json`.
