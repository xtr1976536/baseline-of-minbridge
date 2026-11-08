import unittest

from verifiqa.question_filter import is_numerical_question
from verifiqa.types import FinanceBenchExample


class QuestionFilterTests(unittest.TestCase):
    def test_direct_metric_questions_are_in_scope(self):
        self.assertTrue(is_numerical_question(
            "What is the FY2018 capital expenditure amount (in USD millions) for 3M?",
            "$1577.00",
        ))
        self.assertTrue(is_numerical_question(
            "Assume that you are a public equities analyst. Answer the following question "
            "by primarily using information that is shown in the balance sheet: what is "
            "the year end FY2018 net PPNE for 3M? Answer in USD billions.",
            "$8.70",
        ))
        self.assertTrue(is_numerical_question(
            "Based on the information provided, what is AES's FY2022 return on assets "
            "(ROA)? Round your answer to two decimal places.",
            "-0.02",
        ))

    def test_finqa_portion_question_is_numeric(self):
        self.assertTrue(is_numerical_question(
            "what portion of total purchase price is related to stock awards?",
            "0.02899",
        ))

    def test_qualitative_questions_with_numbers_are_out_of_scope(self):
        self.assertFalse(is_numerical_question(
            "Is 3M a capital-intensive business based on FY2022 data?",
            "No. CAPEX/Revenue Ratio: 5.1%; Fixed assets/Total Assets: 20%",
        ))
        self.assertFalse(is_numerical_question(
            "What drove operating margin change as of FY2022 for 3M?",
            "Operating Margin decreased by 1.7%",
        ))
        self.assertFalse(is_numerical_question(
            "If we exclude the impact of M&A, which segment has dragged down 3M's "
            "overall growth in 2022?",
            "The consumer segment shrunk by 0.9% organically.",
        ))
        self.assertFalse(is_numerical_question(
            "In 2022 Q2, which of JPM's business segments had the highest net income?",
            "Corporate & Investment Bank. Its net income was $3725 million.",
        ))
        self.assertFalse(is_numerical_question(
            "Does 3M have a reasonably healthy liquidity profile based on its quick "
            "ratio for Q2 of FY2023?",
            "No. The quick ratio was 0.96.",
        ))
        self.assertFalse(is_numerical_question(
            "At the Pepsico AGM held on May 3, 2023, what was the outcome of the "
            "shareholder vote on the shareholder proposal for a congruency report "
            "by Pepsico on net-zero emissions policies?",
            "The shareholder proposal was defeated.",
        ))
        self.assertFalse(is_numerical_question(
            "What was the outcome of the shareholder vote on the independent Board "
            "Chair proposal?",
            "The proposal was defeated with 250,838,697 votes for.",
        ))
        self.assertFalse(is_numerical_question(
            "What was the key agenda of the AMCOR's 8k filing dated 1st July 2022?",
            "Amcor entered into supplemental indentures.",
        ))
        self.assertFalse(is_numerical_question(
            "What is the nature & purpose of AMCOR's restructuring liability as oF "
            "Q2 of FY2023 close?",
            "87% of the total restructuring liability is related Employee liabilities.",
        ))
        self.assertFalse(is_numerical_question(
            "Has AMCOR's quick ratio improved or declined between FY2023 and FY2022? "
            "If the quick ratio is not something that a financial analyst would ask "
            "about a company like this, then state that and explain why.",
            "The quick ratio has slightly improved from 0.67 times to 0.69 times.",
        ))
        self.assertFalse(is_numerical_question(
            "Does AMCOR have an improving gross margin profile as of FY2023? If gross "
            "margin is not a useful metric for a company like this, then state that "
            "and explain why.",
            "No. For AMCOR there has been a slight decline in gross margins by 0.8%.",
        ))

    def test_missing_question_is_out_of_scope(self):
        example = FinanceBenchExample(financebench_id="x", question="", answer="123")
        self.assertFalse(is_numerical_question(example.question, example.answer))


if __name__ == "__main__":
    unittest.main()
