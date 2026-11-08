"""Initial claim generation with question-led numerical display precision."""
from verifiqa.generation.answer_generator import AnswerGenerator as OriginalGenerator

PRECISION='''
Numerical display instructions (not additional filing evidence):
Follow any rounding explicitly requested by the question. Otherwise preserve the
filing's reported monetary precision when converting units. For computed ratios,
percentages or days with no requested rounding, retain at least six significant
digits in the final number and avoid rounding intermediate calculations. Do not
report multiple alternative final values. These instructions do not supply any
facts, a financial formula, verification feedback or an answer.
'''


class AnswerGenerator(OriginalGenerator):
    def generate(self,question,evidence_chunks,retrieval_plan=None,formula_context=None,feedback=None):
        if formula_context or feedback:raise ValueError('main_generation_forbids_formula_or_verifier_feedback')
        return super().generate(question+PRECISION,evidence_chunks,retrieval_plan=retrieval_plan)
