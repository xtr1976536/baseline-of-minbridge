from decimal import Decimal

import pytest

from gbfr.metrics import canonical,correct,parse_number
from gbfr.units import asks_for_year,normalize_meta,reporting_meta,result_meta,target_meta


def prediction(value,currency=None,scale=None,unit=None):
    return {'status':'answered','value':value,'meta':{'currency':currency,'scale':scale,'unit':unit}}


def sample(answer,question='What was the amount?',context='',answer_meta=None):
    return {'answer':answer,'question':question,'context':context,'answer_meta':answer_meta or {},'unanswerable':False}


def test_explicit_gold_display_units_outrank_an_input_table_scale():
    s=sample('$17.6 million',context='The following table is in thousands. A different disclosure is $17.6 million.')
    assert correct(prediction(17.6,'USD','million'),s,2,'reference_display')
    assert correct(prediction(17600,'USD','thousand'),s,2,'reference_display')
    assert not correct(prediction(17.6,'USD','thousand'),s,2,'reference_display')
    assert not correct(prediction(17.6,'CNY','million'),s,2,'reference_display')


def test_official_gold_display_scale_is_not_overwritten_by_input_scale():
    s=sample(19.7,context='The revenue table is in thousands.',answer_meta={'scale':'million'})
    assert target_meta(s,parse_number(s['answer']).meta)['scale']=='million'
    assert correct(prediction(19700,scale='thousand'),s,2,'reference_display')
    assert not correct(prediction(19.7,scale='thousand'),s,2,'reference_display')


def test_explicit_question_display_units_take_priority_without_factor_search():
    s=sample(12,'What was the amount in US$ m?',context='The source table is in thousands.')
    assert correct(prediction(12000,'USD','thousand'),s,2,'reference_display')
    assert not correct(prediction(12,'USD','thousand'),s,2,'reference_display')
    s=sample(12,'In millions, what was the amount?',context='The source table is in thousands.')
    assert correct(prediction(12,scale='million'),s,2,'reference_display')


def test_mixed_report_declarations_do_not_assign_another_tables_scale():
    doc='Shares awarded (in thousands).\nCompensation expense: $12.1 million.\nAn unrelated payment: $9.0 million.'
    assert reporting_meta(doc)['scale'] is None
    s=sample(21.1,'What was total compensation expense?',doc)
    # An unknown target scale cannot verify an explicit million multiplier
    # merely because the two displayed numbers happen to be identical.
    assert not correct(prediction(21.1,'USD','million'),s,2,'reference_display')
    assert correct(prediction(21.1),s,2,'reference_display')
    assert correct(prediction(21.1,'USD','million'),
                   {**s,'answer_meta':{'currency':'USD','scale':'million'}},2,'reference_display')
    assert not correct(prediction(21100,'USD','thousand'),s,2,'reference_display')
    assert reporting_meta('All amounts in USD thousands. Net revenue: 94.')['scale']=='thousand'


def test_currency_codes_are_tokens_not_substrings_of_geographical_names():
    s=sample(1869.5,'What is average revenue from Europe?',context='Revenue (in thousands): Europe $1,869.5.',answer_meta={'scale':'thousand'})
    assert target_meta(s,{})['currency'] is None
    assert correct(prediction(1869.5,'USD','thousand'),s,2,'reference_display')
    s=sample(1869.5,'What is average revenue in EUR?',answer_meta={'scale':'thousand'})
    assert not correct(prediction(1869.5,'USD','thousand'),s,2,'reference_display')


@pytest.mark.parametrize('q',[
    'Which year had the lowest percentage difference in earnings per share?',
    'In which year was the dividend paid per ordinary share in € the largest?',
    'What fiscal year recorded the largest USD revenue?',
])
def test_a_selected_year_does_not_inherit_the_measures_currency_or_unit(q):
    s=sample('2019',q,'All values in USD millions.')
    assert target_meta(s,{})=={'currency':None,'scale':None,'unit':'years'}
    assert correct(prediction(2019,unit='years'),s,2,'reference_display')
    assert result_meta({'currency':'USD','scale':'million','unit':'currency/share'},'sum',query=q)=={
        'currency':None,'scale':None,'unit':'years'}


@pytest.mark.parametrize('q',["What year's revenue was largest?",'What year-over-year revenue change was reported?',
    'What year over year revenue growth was reported?','What year-on-year revenue increase was reported?'])
def test_year_words_do_not_always_request_a_year_identifier(q):
    assert not asks_for_year(q)
    assert result_meta({'currency':'USD','scale':'million','unit':None},'sum',query=q)['scale']=='million'


def test_count_of_rows_ignores_threshold_currency_and_underlying_report_scale():
    for q in ['In 2019, how many quarters did the high share price exceed $85?',
              'How many contractual obligations had payments above $500,000 thousand?',
              'How many remuneration key performance indicators used the Annual Incentive Plan?']:
        s=sample('2',q,'Amounts in GBP millions.')
        assert correct(prediction(2,scale='ones',unit='count'),s,2,'reference_display')
        assert not correct(prediction(2,'GBP','million'),s,2,'reference_display')


def test_count_of_years_accepts_year_labels_but_not_another_counted_unit():
    s=sample('2','How many years did revenue exceed $10 million?','Revenue is in USD millions.')
    assert correct(prediction(2,unit='count'),s,2,'reference_display')
    assert correct(prediction(2,unit='years'),s,2,'reference_display')
    assert not correct(prediction(2,unit='quarters'),s,2,'reference_display')
    assert not correct(prediction(2,'USD',unit='years'),s,2,'reference_display')


def test_count_quantity_is_not_an_input_per_share_amount_or_a_percentage_of_count():
    s=sample(9521.67,'What is the average number of potential common shares excluded from diluted net loss per share?',answer_meta={'scale':'thousand'})
    assert correct(prediction(9521.666,'', 'thousand','shares'),s,2,'reference_display')
    s=sample('93.6%','What percentage of the total number of shares were repurchased?')
    assert correct(prediction(93.571,unit='percentage'),s,2,'reference_display')


def test_an_input_price_does_not_make_total_option_value_a_per_share_output():
    s=sample(241.11,'Considering the exercise price, what is the total value of stock options in millions of dollars?')
    assert target_meta(s,{})['unit'] is None
    assert correct(prediction(241.11,'USD','million'),s,2,'reference_display')
    assert not correct(prediction(241.11,'USD',None,'currency/share'),s,2,'reference_display')


def test_quoted_percentage_in_a_bond_coupon_is_an_input_not_answer_dimension():
    s=sample(60375000,'What is the annual interest cost savings from redeeming the 8.75% notes?')
    assert target_meta(s,{})['unit'] is None
    assert correct(prediction(60.375,'USD','million'),{**s,'answer_meta':{'scale':'ones'}},2,'reference_display')


def test_percent_symbol_query_and_proportion_alias_are_dimensionless():
    s=sample(7,'What is the change in the % of revenue?',answer_meta={'scale':'thousand'})
    assert correct(prediction(7,unit='percentage'),s,2,'reference_display')
    s=sample(.65,'What is the proportion of finished goods to total inventory?')
    assert correct(prediction(.6485,unit='proportion'),s,2,'reference_display')


def test_redundant_ratio_in_scale_field_is_a_syntactic_unit_alias_only():
    assert normalize_meta({'scale':'ratio','unit':'ratio'})=={'currency':None,'scale':None,'unit':'ratio'}
    assert canonical(Decimal('.61'),{'scale':'ratio','unit':'ratio'})[0]==Decimal('.61')
    with pytest.raises(ValueError):normalize_meta({'scale':'ratio','unit':'percentage'})
    with pytest.raises(ValueError):normalize_meta({'scale':'not a known scale'})


def test_warrant_and_ordinary_share_prices_are_not_the_same_dimension():
    s=sample('7.47','What was the share price of warrants exercised?')
    assert correct(prediction(7.4745,'USD','ones','dollars per warrant'),s,2,'reference_display')
    assert not correct(prediction(7.4745,'USD','ones','currency/share'),s,2,'reference_display')
    s=sample(.1,'What was the change in dividend paid per ordinary share in €?')
    assert correct(prediction(.1,'EUR',unit='per ordinary share'),s,2,'reference_display')
