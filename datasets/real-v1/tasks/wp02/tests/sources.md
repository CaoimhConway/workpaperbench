# Export dictionary
Authored synthetic ledger. export_row identifies a copied export record. event_id is the stable event identity. tx_id identifies the transaction containing the event. Copies of an event have identical economic fields. amount_units is an integer in whole token units, not USD.

The transfer definition counts every distinct event whose event_kind is transfer. Mint and burn events do not contribute. Event identity governs export copies. All supplied rows share one fixed population and period.

This new synthetic control includes equal amounts on different legitimate event identities. It is not observed chain data.
