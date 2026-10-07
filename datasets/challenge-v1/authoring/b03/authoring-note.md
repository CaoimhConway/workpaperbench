# Private authoring note

## Source, scope, and rights

The detailed issuer-hosted Financial Figures and Reserves Report is retained locally as `tether-ffrr-2025-06.pdf`. Source URL: https://assets.ctfassets.net/vyse88cgwfbl/2SGAAXnsb1wKByIzkhcbSx/9efa4682b3cd4c62d87a4c88ee729693/ISAE_3000R_-_Opinion_Tether_International_Financial_Figure_RC187322025BD0201.pdf. Bytes: 481,226. SHA-256: `4b3c20f9492838a12d686af4d59271d6d6bdf937dadf256d62ae125ecca1b13b`. Local file modification time: 2026-10-06T22:14:44.710917Z, which is not original server metadata. The report is authorized and approved July 31, 2025. The historical PDF publication timestamp is unknown. The original official release is retained as `tether-july-2025-release-original.html` with its retrieval metadata in the adjacent `.metadata.json`. The release's stated publication date is July 31, 2025, and its publication time is unknown. Rights were not identified for redistribution of the full report or release, so only facts, concise paraphrases, and source locators are retained.

## Independent Decimal calculations

The eleven detailed June 30 reserve components sum to USD 162,574,933,798. The detailed report's exact company-wide liabilities are USD 157,108,000,474. Component-derived assets less the detailed company-wide liability amount equal USD 5,466,933,324. Gross contractual redemption is USD 157,571,645,333. The report's company-held tokens outside the Treasury wallet are USD 471,389,476. Gross redemption less that held amount is USD 157,100,255,857.

The July release says company total liabilities of USD 157,108,009,474. Oriented as release minus detailed FFR, the delta is USD +9,000. The bounded proposition that the publications report identical exact June 30 company liabilities is contradicted.

## Scope, alternatives, and plausible errors

The asset reconstruction can sum the eleven categories directly or aggregate an equivalent long-form line-item table. The company excess uses detailed report company-wide liabilities. The token-liability derivation uses the gross redemption amount and the specific company-held tokens outside the Treasury wallet, it is not the same amount as company total liabilities. The publication comparison must keep detailed FFR and release liability fields distinct and preserve the requested subtraction direction.

Do not use the rounded USD-million summary in place of exact line items, use December comparative figures whose entity scope differs, treat company total liabilities as the token liability, or combine the company-held amount with other Treasury wallet categories. The report describes financial information extracted from records and is not a set of full financial statements. A component sum and company-wide excess do not establish liquidity, liquidation proceeds, or legal enforceability.

## Synthetic controls

`bitcoin_fair_value_change` increases the Bitcoin component by USD 250,000. It changes reconstructed reserve assets and the excess over company total liabilities, while net token liability and the cross-publication liability delta remain unchanged.

`company_held_token_change` increases the company-held token amount by USD 1,000. It changes the derived net token liability while leaving company-wide liabilities and reserve assets unchanged.

`release_liability_alignment` reduces only the release company total-liabilities field by USD 9,000 to match the detailed report amount. It makes the oriented delta zero and changes the bounded proposition to supported. Other claims are unchanged.

## Candidate-only shortcut audit

The request names four IDs and units, specifies the period, source scopes, and difference orientation. It does not give totals for the requested reconstruction, an answer formula as SQL, or a verdict. Candidate evidence contains only the source values needed for the requested claims. The exact company-liability discrepancy is a source fact required for the comparison, not a precomputed requested delta.
## Accepted evidence paths

The reserve-component reconstruction accepts `b03:s02` alone, with `b03:s01` accepted as added report-date and company-scope context. The net token liability accepts its footnote section `b03:s04`, with `b03:s01` as added context. Company asset excess accepts `b03:s02` and `b03:s03`, optionally with `b03:s01`. The release delta and bounded comparison accept `b03:s03` and `b03:s05`, optionally with `b03:s01` for detailed-report scope and date.
