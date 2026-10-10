"""Freeze a construction track using the same dossiers and financial targets."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash
from review_workflow import seal, write_json

DATASET = 'workflow-v8'
INTRODUCTIONS = {
    'a01': 'Build a fiscal-quarter SQL workpaper for Microsoft FY2025 Q2 and the disclosed FY2024 comparison. Derive the first quarter of each fiscal year from six-month statements, calculate sequential operating-margin changes, and compare Azure constant-currency growth with the earlier Q2 guidance range. Keep Azure and Intelligent Cloud operating-income scope distinct.',
    'a02': 'Build the Meta cash-generation and segment workpaper for FY2024 and FY2025. Reconstruct the first nine months from full-year and Q4 disclosures, and report Q4, first-nine-month and annual outputs for both years. Reconcile operating cash flow from net income, noncash adjustments and operating working-capital changes. Apply the issuer free-cash-flow definition, including finance-lease principal. Calculate both segment margins without double-counting advertising within Family of Apps.',
    'a03': 'Build the Circle workpaper through FY2025 under both disclosed adjusted-expense definitions. Include the seven disclosed annual/quarterly periods and reconstruct first-nine-month expense bridges for FY2024 and FY2025. Attribute the annual change in additional exclusions by component. Reconcile reserve and other income with distribution costs, then calculate the two issuer-defined margins for FY2024, FY2025 and both Q4 comparisons. Keep definition changes separate from an economic improvement claim.',
    'a04': 'Build Amazon cash-generation and capital-funding analysis for FY2024, FY2025 and both Q4 periods. Reconstruct nine-month flows and reconcile total cash movement. Apply the issuer net-property-spending definition before showing separate analyst cash-flow measures after finance-lease and financing-obligation principal. Keep supplemental noncash acquisition observations outside cash spending.',
    'a05': 'Build Costco FY2025 operating and membership workpapers. Include both 16-week quarters and 52-week years, reconstruct first 36 weeks, and separate merchandise gross profit from membership fees. Attribute operating-income growth to merchandise margin dollars, earned fees and SG&A. Add a clearly labeled mechanical membership accrual bridge while deciding whether it identifies actual cash collections.',
    'a06': 'Build Walmart earnings workpapers through Q3FY2026. Include both Q3 and nine-month comparisons and reconstruct first-six-month earnings outputs. Reconcile signed legal, PhonePe and reorganization adjustments before applying the adjusted currency bridge. Keep year-to-date cash flow in its nine-month scope and assess whether quarter cash flow can be reconstructed.',
    'a07': 'Build NVIDIA gross-profit and cash-generation workpapers through Q2FY2026. Reconstruct Q1 for both years from first-half and Q2 inputs, calculate standard gross-profit bases, and add the current-year H20 charge/release bridge without treating missing prior exclusions as zero. Reconcile issuer cash generation and assess the geographical and forward-looking H20 statements.',
    'a08': 'Build Salesforce FY2026 earnings workpapers with Q4 and annual comparisons and reconstructed first nine months. Reconcile operating and below-operating income, avoid double-counting restructuring SBC, and produce a labeled acquisition-scope revenue bridge without overstating an organic currency-adjusted conclusion.',
    'a09': 'Build Disney FY2025 segment and consolidated workpapers through Q4 and derive first nine months for both years. Reconcile intersegment revenue and segment profit to GAAP pretax income. Keep the subscription comparison sequential and labeled as service subscriptions, and assess the change from consolidated Star India to equity-method ownership.',
    'a10': 'Build American Express FY2025 payment-economics workpapers using the seven-period income statements and both release and statistical supplement. Reconcile revenue to earnings, attribute annual and Q4 revenue growth by component, and produce reported/FX growth plus the implied processed-volume bridge while respecting source scope.',
    'b01': 'Build an SBC reserve workpaper from the May and June 2025 reserve reports. Calculate coverage and residuals by economic observation date and calendar days from observation to report signature. Bridge cash, government-debt, reserve and circulation changes from May to June. Treat repeated identical exports as one report, while keeping different economic dates distinct even when their amounts are equal. Determine whether these snapshots identify payments volume.',
    'b02': 'Build a PYUSD valuation workpaper from the January and February 2026 reports. Report coverage at January 30, February 10 and February 27 at their disclosed observation times. Reconcile Treasury holdings at fair value to the reported asset category, show separate par and cost comparisons, and build adjacent stock-change bridges. Address the January 16 date conflict without assigning an invented year. Do not count repo collateral as additional Treasury assets.',
    'b03': 'Build a Coinbase revenue-yield workpaper through FY2025. Produce the annual revenue contribution bridge using recast categories and corporate interest. Calculate quarterly and annualized USDC booked-revenue ratios separately on and off platform. Show the consumer and institutional Q4 revenue-to-spot-volume proxies, but resolve whether those proxies identify commission rates. Do not mix total derivative notional with spot volume or treat a condensed disclosure as zero.',
    'b04': 'Build a Robinhood FY2025 financial workpaper. Reconcile adjusted expenses, including negative prior settlement amounts and both the reported and a consistently credit-excluded expense basis. Attribute annual revenue growth across transaction, interest and other revenue. Separate app and Bitstamp crypto volume in Q4 and preliminary January, normalizing duration only as a monthly arithmetic average. Resolve the scope of any organic asset-growth inference.',
    'b05': 'Build a PayPal engagement and margin workpaper through FY2025. Include all five quarter rows, distinguish quarterly from trailing-year engagement, and reconstruct the annual activity and revenue bridge from four quarters. Reconcile transaction margin and its customer-interest exclusion for both annual and Q4 comparisons. Report rounding residuals instead of forcing them to zero, and distinguish payment value, recognized revenue and account activity.',
    'b06': 'Build a Q4FY2025 platform-metric workpaper against the prior Q4. Calculate segment revenue and booking ratios, reconcile the segment EBITDA sum through corporate costs, and calculate monthly consumer activity. Report descriptive segment ratios without turning them into contractual commissions.',
    'b07': 'Build Airbnb booking and cash-conversion workpapers through FY2025. Produce eight quarterly outputs, retain the discrepancy between rounded-input ADR and reported ADR, and calculate the four FY2025 rolling cash windows. Distinguish the hybrid booked unit, revenue recognition timing, implied take rate and same-period financial margins.',
    'b08': 'Build Shopify FY2025 category-economics, cash-conversion and subscription-stock workpapers. Include FY2024 and Q4 comparisons, reconstruct nine-month financial flows, calculate the exit-MRR annual run rate, and compare it with actual subscription revenue without presenting the difference as missing revenue. Assess whether the merchant revenue/GMV ratio identifies a payments fee.',
    'b09': 'Build Intuit FY2025 adjusted-metric workpapers including all FY2024 quarters and both full years. Reconcile operating and net-income exclusion scopes separately, compute matching diluted EPS and quantify the denominator effect. Determine whether the new exclusions permit an exact prior-year restatement.',
    'b10': 'Build Berkshire FY2025 research bridges with FY2024/FY2023 comparisons. Separate parent-attributable operating earnings from consolidated earnings, reconcile consolidated operating cash, and tie the pretax investment-gain components to their cash-flow removal. Assess the limits of interpreting gains and float stocks as economic cash returns.',
    'c01': "Build an annual consolidated revenue and gross-profit attribution for Block using the FY2024 filing and its own FY2023 comparator. Show each revenue category's change, contribution to total revenue growth, annual shares and share change. Build a gross-profit bridge including acquired-technology amortization, reconcile both bridges to reported totals, and quantify Bitcoin gross-profit growth. Determine whether Bitcoin explains a majority of consolidated revenue growth and assess the stated claim about the contribution of higher Bitcoin prices.",
    'c02': 'Reconcile Adobe FY2025 GAAP and adjusted operating performance before using next-year ARR guidance. Include each disclosed quarterly comparison, quantify the annual change in the adjustment gap by component, and show why growth rates differ. Build an ARR basis bridge from observed FY2025 exit to revalued FY2026 opening and the mechanically implied target on the disclosed growth basis. Keep forecasts and ARR stock measures distinct from recognized revenue.',
    'c03': 'Reconcile Visa FY2025 revenue and earnings before attributing operating improvement. Build the current annual, Q4 and reconstructed nine-month gross-to-net bridge, preserving signed client incentives. Reconcile after-tax net-income adjustments for both years and both Q4 comparisons, then show how GAAP and adjusted growth diverge. Distinguish litigation exclusions from recurring revenue economics and respect service-revenue timing.',
    'c04': 'Produce a Mastercard FY2025 attribution workpaper using the branded operational tables and company financial reconciliations. Attribute annual and Q4 worldwide purchase-volume growth to five mutually exclusive regions, compare average purchase sizes, and reconcile regional totals with worldwide rows. Preserve source-rounding residuals and avoid adding subtotal or credit/debit partitions twice. Reconcile company operating margins separately from the operational measures.',
    'c05': 'Reconcile Apple FY2025 and Q4 earnings growth across category profitability, operating expenses, signed other income and tax. Include both years, attribute the net-income change by component, and compare current GAAP income with both prior GAAP and the explicitly adjusted prior tax baseline.',
    'c06': 'Reconcile Alphabet Q2FY2025 year-over-year and sequential revenue growth. Apply comparison-specific translation bases, separate currency from hedging, and attribute reported year-over-year growth across mutually exclusive revenue components. Assess the limit on a separate AI-product attribution.',
    'c07': 'Reconcile Cisco FY2025 as first released with the superseding annual report. Include FY2024, build each financial version, isolate the supplier settlement charge and tax benefit, and reconcile the changed operating-cash components. Keep signatures, economic dates, publication precision and cash versus expense distinct.',
    'c08': 'Reconcile Broadcom FY2025, both supplied Q4 periods and Q3FY2025. Calculate signed adjusted net income, match diluted share bases and quantify the effect of using an incorrect GAAP denominator. Attribute annual and Q4 revenue growth by segment while separating tax, discontinued-operation and price-attribution scope.',
    'c09': 'Reconcile JPMorgan FY2025 and Q4 managed presentation, adjusted overhead and significant-item exclusions. Preserve rounding residuals from printed slide inputs. Derive the implied after-tax First Republic exclusion from the disclosed combined annual change, distinguishing that derivation from a printed observation.',
    'c10': 'Reconcile Netflix FY2025 currency presentation with the FY2026 forecast. Use detailed Q4 regional precision, distinguish the annual beginning-year margin basis, and build low/high forecast implications using the reported FY2025 baseline. Assess the acquisition-expense and membership-denominator limits.',
}
BRALE_CLAIMS = {
    'claim_2': 'The June report was signed more calendar days after its economic observation than the May report.',
    'claim_3': 'At least one observation date shows reserve assets greater than issued SBC units at USD 1 per token.',
}
BRALE_DATE_EVIDENCE = [[f'b01:s0{may}', f'b01:s0{june}']
                       for may in (1, 2, 3) for june in (4, 5, 6)]
BRALE_EVIDENCE_REVISION = {
    'outputs': ['tables.signature_lag', 'claims.claim_2'],
    'sufficient_evidence': BRALE_DATE_EVIDENCE,
    'reason': 'Every supplied evidence entry includes its report observation period and report_signed_date. Any May entry paired with any June entry supports the two signature lags and their comparison.',
}


def construct(destination):
    prior = load(ROOT, 'workflow-v7')
    if set(prior['tasks']) != set(INTRODUCTIONS):
        raise ValueError('construction_task_set_changed')
    manifest = copy.deepcopy(prior)
    manifest.update(dataset_id=DATASET, prior_catalog=prior['manifest_id'],
        evaluation_track='construction', execution_profile='isolated-linux',
        status='Software and authored controls only, no model evaluation of this construction track',
        construction_revision={
            'maintenance_catalog': prior['manifest_id'], 'starting_sql_supplied': False,
            'financial_inputs_changed': False, 'financial_targets_changed': False,
            'controls_changed': False, 'scorer_changed': False, 'new_inference': False,
            'claim_assertion_changes': {'b01': BRALE_CLAIMS},
            'claim_change_reason': 'Replace assertions about removed starting SQL with source-grounded date and coverage assertions. Verdicts are unchanged.',
            'evidence_support_changes': {'b01': BRALE_EVIDENCE_REVISION},
            'interpretation': 'Construction and maintenance are separate conditions. No starting-SQL transitions apply to construction.'})
    for key, old in prior['tasks'].items():
        _, _, source = load(ROOT, 'workflow-v7', key)
        task = destination / 'tasks' / key
        shutil.copytree(source, task)
        identifier = DATASET + '-' + key
        for path in task.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.md', '.toml', '.sh'):
                path.write_text(path.read_text().replace(old['task_id'], identifier))
        gold = json.loads((task / 'tests/gold.json').read_text())
        starting = list((task / 'environment').glob('starting_*.sql'))
        if {path.name for path in starting} != {'starting_' + name + '.sql' for name in gold['tables']}:
            raise ValueError('construction_starting_set_changed:' + key)
        dockerfile = task / 'environment/Dockerfile'
        docker = dockerfile.read_text()
        for path in starting:
            if docker.count(' ' + path.name) != 1:
                raise ValueError('construction_copy_anchor_changed:' + key)
            docker = docker.replace(' ' + path.name, '')
            path.unlink()
        dockerfile.write_text(docker)
        instruction = task / 'instruction.md'
        paragraphs = instruction.read_text().split('\n\n')
        paragraphs[1] = INTRODUCTIONS[key]
        anchor = 'The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.'
        if paragraphs[2].count(anchor) != 1:
            raise ValueError('construction_instruction_anchor_changed:' + key)
        paragraphs[2] = paragraphs[2].replace(anchor,
            'Construct all requested SQL from these observations. This construction track supplies no starting SQL.')
        instruction.write_text('\n\n'.join(paragraphs))
        if key == 'b01':
            contract = json.loads((task / 'environment/output_contract.json').read_text())
            if not all('starting_' in contract['claim_assertions'][name] for name in BRALE_CLAIMS):
                raise ValueError('construction_claim_anchor_changed')
            contract['claim_assertions'].update(BRALE_CLAIMS)
            write_json(task / 'environment/output_contract.json', contract)
            gold['tables']['signature_lag']['evidence'] = copy.deepcopy(BRALE_DATE_EVIDENCE)
            gold['claims']['claim_2']['evidence'] = copy.deepcopy(BRALE_DATE_EVIDENCE)
        authoring = json.loads((task / 'authoring.json').read_text())
        authoring['construction_revision'] = {
            'prior_task_sha256': old['task_sha256'],
            'maintenance_rationale': authoring['rationale'],
            'maintenance_starting_defects': authoring['starting_defects'],
            'removed_starting_files': sorted(path.name for path in starting),
            'claim_assertion_changes': BRALE_CLAIMS if key == 'b01' else {},
            'evidence_support_changes': BRALE_EVIDENCE_REVISION if key == 'b01' else {}}
        authoring.update(evaluation_track='construction', rationale=INTRODUCTIONS[key],
                         starting_defects='not applicable - no starting SQL supplied')
        write_json(task / 'authoring.json', authoring)
        seal(task, gold)
        manifest['tasks'][key].update(task_id=identifier, evaluation_track='construction',
            path='datasets/' + DATASET + '/tasks/' + key, task_sha256=tree_hash(task))
    manifest['hashes']['scripts/build_workflow_construction.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = DATASET + '-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json', manifest)
    return manifest


def build(check):
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        manifest = construct(stage)
        expected = {path.relative_to(stage) for path in stage.rglob('*') if path.is_file()}
        output = ROOT / 'datasets' / DATASET
        existing = {path.relative_to(output) for path in output.rglob('*') if path.is_file()}
        if existing - expected:
            raise ValueError('construction_catalog_unexpected_files')
        for relative in sorted(expected):
            path, target = stage / relative, output / relative
            if check:
                if not target.is_file() or target.read_bytes() != path.read_bytes():
                    raise ValueError('construction_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and target.read_bytes() != path.read_bytes():
                    raise ValueError('construction_catalog_already_exists')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'], len(manifest['tasks']), 'construction cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    build(parser.parse_args().check)
