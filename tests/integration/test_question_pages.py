import pytest
import html
import re


from tests.factories import ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    consultation = ConsultationFactory(
        with_question=True, with_question__with_answer=True, with_question__with_multiple_choice=True
    )
    section = consultation.section_set.first()
    question = section.question_set.first()
    answer = question.answer_set.first()
    question_summary_url = f"/consultations/{consultation.slug}/sections/{section.slug}/questions/{question.slug}"
    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content
    assert answer.theme.summary in page_content

    for keyword in answer.theme.keywords:
        assert keyword in page_content

    for option in question.multiple_choice_options:
        assert option in page_content

    percentages = re.findall(r"\d+%", page_content)
    count = 0
    for percentage in percentages:
        percentage_num = float(percentage.replace("%", ""))
        count += percentage_num
    assert count == 100
