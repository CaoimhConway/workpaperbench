"""Independent references for compensation scope and consolidated cash bridges."""
import copy
from decimal import Decimal
from build_workflow_tasks import INTEGER, TEXT, numeric, table
from workflow_development_cases import claim
D=lambda v:Decimal(str(v))
M=numeric('usd_million',0.001)
P=numeric('percent')
U=numeric('usd_per_share')
S=numeric('million_shares')


def intuit(data):
    operating=[]
    income=[]
    shares=[]
    for r in data['income_bases']:
        if r['fiscal_year'] not in (2024,2025) or r['window'] not in ('Q1','Q2','Q3','Q4','FY'):continue
        matching=[a for a in data['adjustments'] if a['fiscal_year']==r['fiscal_year'] and a['window']==r['window']]
        op_change=sum((D(a['signed_adjustment_usd_million']) for a in matching if a['scope']=='operating_and_income'),D(0))
        ni_change=sum((D(a['signed_adjustment_usd_million']) for a in matching),D(0))
        gaap_op=D(r['gaap_operating_usd_million'])
        gaap_ni=D(r['gaap_income_usd_million'])
        adjusted_op=gaap_op+op_change
        adjusted_ni=gaap_ni+ni_change
        operating.append([r['fiscal_year'],r['window'],float(gaap_op),float(op_change),float(adjusted_op),float(adjusted_op-D(r['reported_adjusted_operating_usd_million']))])
        income.append([r['fiscal_year'],r['window'],float(gaap_ni),float(ni_change),float(adjusted_ni),float(adjusted_ni-D(r['reported_adjusted_income_usd_million']))])
        gs,ns=D(r['gaap_shares_million']),D(r['adjusted_shares_million'])
        shares.append([r['fiscal_year'],r['window'],float(gs),float(ns),float(gaap_ni/gs),float(adjusted_ni/ns),float(adjusted_ni/gs),float(adjusted_ni/ns-adjusted_ni/gs)])
    return {'operating_reconciliation':operating,'income_reconciliation':income,'share_basis':shares}

INT_OP="""SELECT b.fiscal_year,b.window,b.gaap_operating_usd_million,SUM(a.signed_adjustment_usd_million) signed_exclusion_usd_million,
b.gaap_operating_usd_million+SUM(a.signed_adjustment_usd_million) adjusted_operating_usd_million,
b.gaap_operating_usd_million+SUM(a.signed_adjustment_usd_million)-b.reported_adjusted_operating_usd_million residual_usd_million
FROM income_bases b JOIN adjustments a USING(fiscal_year,window) WHERE b.fiscal_year IN (2024,2025) AND b.window IN ('Q1','Q2','Q3','Q4','FY')
AND a.scope='operating_and_income' GROUP BY b.fiscal_year,b.window"""
INT_NI="""SELECT b.fiscal_year,b.window,b.gaap_income_usd_million,SUM(a.signed_adjustment_usd_million) signed_exclusion_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN adjustments a USING(fiscal_year,window) WHERE b.fiscal_year IN (2024,2025) AND b.window IN ('Q1','Q2','Q3','Q4','FY') GROUP BY b.fiscal_year,b.window"""
INT_SHARES="""WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_adjustment_usd_million) adjusted FROM income_bases b JOIN adjustments a USING(fiscal_year,window)
GROUP BY b.fiscal_year,b.window) SELECT fiscal_year,window,gaap_shares_million,adjusted_shares_million,
1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,1.0*adjusted/adjusted_shares_million computed_adjusted_eps_usd,
1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,1.0*adjusted/adjusted_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE fiscal_year IN (2024,2025) AND window IN ('Q1','Q2','Q3','Q4','FY')"""


def berkshire(data):
    earnings=[]
    cash=[]
    investment=[]
    for b in data['annual_bases']:
        year=b['year']
        if year not in (2023,2024,2025):continue
        components={r['measure']:D(r['aftertax_parent_usd_million']) for r in data['earnings_components'] if r['year']==year}
        total=sum(components.values(),D(0))
        gain,impairment=components['investment_gain'],components['impairment']
        operating=total-gain-impairment
        earnings.append([year,float(total),float(gain),float(impairment),float(operating),float(total-D(b['reported_parent_income_usd_million']))])
        consolidated=D(b['consolidated_income_usd_million'])
        parent=D(b['reported_parent_income_usd_million'])
        adjustment=sum((D(r['signed_cash_adjustment_usd_million']) for r in data['cash_adjustments'] if r['year']==year),D(0))
        cash.append([year,float(parent),float(consolidated),float(consolidated-parent),float(adjustment),float(consolidated+adjustment),float(consolidated+adjustment-D(b['reported_operating_cash_usd_million']))])
        gains={r['measure']:D(r['pretax_gain_usd_million']) for r in data['investment_components'] if r['year']==year}
        net=sum(gains.values(),D(0))
        cf=next(D(r['signed_cash_adjustment_usd_million']) for r in data['cash_adjustments'] if r['year']==year and r['measure']=='investment_gain')
        investment.append([year,float(gains['equity_unrealized']),float(gains['equity_sold']),float(gains['fixed_realized_gain']+gains['fixed_realized_loss']),float(gains['other']),float(net),float(net+cf),float(100*gains['equity_unrealized']/net)])
    return {'parent_earnings_bridge':earnings,'consolidated_cash_bridge':cash,'investment_gain_bridge':investment}

BR_EARN="""WITH p AS (SELECT year,SUM(aftertax_parent_usd_million) total,
SUM(CASE WHEN measure='investment_gain' THEN aftertax_parent_usd_million ELSE 0 END) gain,
SUM(CASE WHEN measure='impairment' THEN aftertax_parent_usd_million ELSE 0 END) impairment FROM earnings_components GROUP BY year)
SELECT p.year,p.total parent_income_usd_million,p.gain investment_gain_usd_million,p.impairment signed_impairment_usd_million,
p.total-p.gain-p.impairment operating_earnings_usd_million,p.total-b.reported_parent_income_usd_million residual_usd_million
FROM p JOIN annual_bases b USING(year) WHERE p.year IN (2023,2024,2025)"""
BR_CASH="""SELECT b.year,b.reported_parent_income_usd_million parent_income_usd_million,b.consolidated_income_usd_million,
b.consolidated_income_usd_million-b.reported_parent_income_usd_million noncontrolling_income_usd_million,
SUM(a.signed_cash_adjustment_usd_million) signed_adjustment_usd_million,
b.consolidated_income_usd_million+SUM(a.signed_cash_adjustment_usd_million) operating_cash_usd_million,
b.consolidated_income_usd_million+SUM(a.signed_cash_adjustment_usd_million)-b.reported_operating_cash_usd_million residual_usd_million
FROM annual_bases b JOIN cash_adjustments a USING(year) WHERE b.year IN (2023,2024,2025) GROUP BY b.year"""
BR_INV="""WITH p AS (SELECT year,SUM(CASE WHEN measure='equity_unrealized' THEN pretax_gain_usd_million ELSE 0 END) unrealized,
SUM(CASE WHEN measure='equity_sold' THEN pretax_gain_usd_million ELSE 0 END) sold,
SUM(CASE WHEN measure IN ('fixed_realized_gain','fixed_realized_loss') THEN pretax_gain_usd_million ELSE 0 END) fixed,
SUM(CASE WHEN measure='other' THEN pretax_gain_usd_million ELSE 0 END) other,SUM(pretax_gain_usd_million) total FROM investment_components GROUP BY year)
SELECT p.year,p.unrealized unrealized_equity_gain_usd_million,p.sold equity_sold_gain_usd_million,p.fixed fixed_net_gain_usd_million,p.other other_gain_usd_million,
p.total pretax_gain_usd_million,p.total+c.signed_cash_adjustment_usd_million cash_removal_residual_usd_million,
100.0*p.unrealized/p.total unrealized_to_net_gain_pct FROM p JOIN cash_adjustments c ON p.year=c.year AND c.measure='investment_gain' WHERE p.year IN (2023,2024,2025)"""


def specifications():
    period={'fiscal_year':INTEGER,'window':TEXT}
    return {
      'b09':{'source':'intuit-fy2025','split':'evaluation','calculate':intuit,
        'tables':{'operating_reconciliation':table(dict(period,gaap_operating_usd_million=M,signed_exclusion_usd_million=M,adjusted_operating_usd_million=M,residual_usd_million=M),['fiscal_year','window'],[['b09:s01','b09:s02']]),
          'income_reconciliation':table(dict(period,gaap_income_usd_million=M,signed_exclusion_usd_million=M,adjusted_income_usd_million=M,residual_usd_million=M),['fiscal_year','window'],[['b09:s01','b09:s02']]),
          'share_basis':table(dict(period,gaap_shares_million=S,adjusted_shares_million=S,computed_gaap_eps_usd=U,computed_adjusted_eps_usd=U,adjusted_income_over_gaap_shares_usd=U,denominator_effect_usd=U),['fiscal_year','window'],[['b09:s01','b09:s03']])},
        'sql':{'operating_reconciliation':INT_OP,'income_reconciliation':INT_NI,'share_basis':INT_SHARES},
        'starting':{'operating_reconciliation':INT_OP.replace("a.scope='operating_and_income'","(a.scope='operating_and_income' OR a.measure='deferred_asset')")},
        'claims':{'deferred_rows_cancel_exactly':claim('contradicted',['b09:s01'],'The FY2025 deferred-plan asset and liability exclusions cancel exactly in the net-income bridge.'),
          'loss_period_share_bases_differ':claim('supported',['b09:s01','b09:s03'],'The FY2024 Q4 adjusted EPS requires a different share denominator from GAAP EPS.'),
          'exact_prior_restatement_identified':claim('unresolved',['b09:s02'],'The dossier identifies exact FY2024 non-GAAP income restated to the new deferred-plan exclusion basis.')},
        'request':'Audit and repair Intuit FY2025 adjusted metrics while preserving all FY2024 quarters and both full years. Reconcile operating and net-income exclusion scopes separately, compute matching diluted EPS and quantify the denominator effect. Determine whether the new exclusions permit an exact prior-year restatement.',
        'definitions':{'operating_reconciliation':'All ten quarter/full-year observations. Include operating-and-income rows only and preserve signed adjustments.',
          'income_reconciliation':'All ten observations. Include operating-and-income plus income-only rows. Residual is recomputed less matching printed adjusted income.',
          'share_basis':'Use recomputed adjusted net income and its matching adjusted diluted denominator. Also report the quotient using GAAP shares and the signed difference. Quotients use rounded source inputs, not rounded published EPS.'},
        'rationale':'The same deferred plan produces adjustments above and below operating income, while a prior GAAP loss changes dilution. Preserving genuine unchanged periods requires financial scope decisions and a supported non-answer to an unavailable restatement.'},
      'b10':{'source':'berkshire-fy2025','split':'evaluation','calculate':berkshire,
        'tables':{'parent_earnings_bridge':table({'year':INTEGER,'parent_income_usd_million':M,'investment_gain_usd_million':M,'signed_impairment_usd_million':M,'operating_earnings_usd_million':M,'residual_usd_million':M},['year'],[['b10:s01']]),
          'consolidated_cash_bridge':table({'year':INTEGER,'parent_income_usd_million':M,'consolidated_income_usd_million':M,'noncontrolling_income_usd_million':M,'signed_adjustment_usd_million':M,'operating_cash_usd_million':M,'residual_usd_million':M},['year'],[['b10:s01','b10:s02']]),
          'investment_gain_bridge':table({'year':INTEGER,'unrealized_equity_gain_usd_million':M,'equity_sold_gain_usd_million':M,'fixed_net_gain_usd_million':M,'other_gain_usd_million':M,'pretax_gain_usd_million':M,'cash_removal_residual_usd_million':M,'unrealized_to_net_gain_pct':P},['year'],[['b10:s02','b10:s03']])},
        'sql':{'parent_earnings_bridge':BR_EARN,'consolidated_cash_bridge':BR_CASH,'investment_gain_bridge':BR_INV},
        'starting':{'consolidated_cash_bridge':BR_CASH.replace('b.consolidated_income_usd_million+SUM(a.signed_cash_adjustment_usd_million)','b.reported_parent_income_usd_million+SUM(a.signed_cash_adjustment_usd_million)')},
        'claims':{'unrealized_exceeds_net_gain':claim('supported',['b10:s03'],'The current-year unrealized equity gain exceeds the total pretax investment gain.'),
          'parent_income_is_cf_start':claim('contradicted',['b10:s01','b10:s02'],'Parent-attributable earnings are the starting net earnings of the consolidated operating-cash bridge.'),
          'exact_float_cost_identified':claim('unresolved',['b10:s03'],'The year-end float stocks identify an exact annual cost of float.')},
        'request':'Repair Berkshire FY2025 research bridges and preserve FY2024/FY2023. Separate parent-attributable operating earnings from consolidated earnings, reconcile consolidated operating cash, and tie the pretax investment-gain components to their cash-flow removal. Assess the limits of interpreting gains and float stocks as economic cash returns.',
        'definitions':{'parent_earnings_bridge':'After-tax parent scope for three years. Operating earnings remove signed investment gains and signed equity-method impairments from parent income.',
          'consolidated_cash_bridge':'Consolidated scope for three years. Add all signed statement adjustments to consolidated net earnings. Noncontrolling income is consolidated less parent income.',
          'investment_gain_bridge':'Pretax scope for three years. Net fixed gains combine realized gains and losses. Compare component total with the signed cash-flow removal and report unrealized equity gain divided by net pretax investment gain.'},
        'rationale':'A report contains parent-only and consolidated statements with superficially similar starting labels. An audit must preserve tax and ownership scopes across three linked reconciliations and resist equating unrealized earnings, sale gains and float stocks with cash flows.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for r in rows:
            for f,v in r.items():
                if isinstance(v,(int,float)) and f not in ('fiscal_year','year'):r[f]=v*2
    yield 'scaled_income_and_matching_denominators',scaled
    changed=copy.deepcopy(data)
    if key=='b09':
        for r in changed['adjustments']:
            if r['fiscal_year']==2025 and r['window'] in ('Q4','FY') and r['measure']=='deferred_asset':r['signed_adjustment_usd_million']-=10
        for r in changed['income_bases']:
            if r['fiscal_year']==2025 and r['window'] in ('Q4','FY'):
                r['gaap_income_usd_million']+=10
        yield 'asset_gain_changes_gaap_income_not_operating_or_adjusted_income',changed
    else:
        for r in changed['annual_bases']:
            if r['year']==2025:
                r['consolidated_income_usd_million']+=50
                r['reported_operating_cash_usd_million']+=50
        yield 'noncontrolling_income_changes_consolidated_not_parent_scope',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        extra=copy.deepcopy(rows)
        for r in extra:r['fiscal_year' if key=='b09' else 'year']+=5
        later[name]+=extra
    yield 'irrelevant_later_periods',later
