# polls/views/analytics.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from ..models import Answer, Choice, Poll, Question, Submission


@login_required
def project_stats(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    total_submissions = Submission.objects.filter(poll=poll).count()

    questions_stats = []
    for q in poll.questions.order_by("order", "id"):
        if q.kind == Question.Kind.TEXT:
            text_answers_count = (
                Answer.objects.filter(submission__poll=poll, question=q)
                .exclude(text_value="")
                .count()
            )
            questions_stats.append({
                "id": q.id,
                "kind": q.kind,
                "text": q.text,
                "text_answers_count": text_answers_count,
                "choices": [],
            })
            continue

        choices = (
            Choice.objects.filter(question=q)
            .annotate(selected_count=Count("answers"))
            .order_by("id")
        )

        total_answers_for_question = choices.aggregate(total=Sum("selected_count"))["total"] or 0
        denom = total_answers_for_question if total_answers_for_question > 0 else 1

        choice_rows = []
        for c in choices:
            percent = round((c.selected_count / denom) * 100)
            choice_rows.append({
                "id": c.id,
                "text": c.text,  # ✅ Правильно: в модели Choice поле называется `text`
                "count": c.selected_count,
                "percent": percent,
            })

        questions_stats.append({
            "id": q.id,
            "kind": q.kind,
            "text": q.text,
            "choices": choice_rows,
        })

    return render(request, "dashboard/project_stats.html", {
        "poll": poll,
        "total_submissions": total_submissions,
        "questions_stats": questions_stats,
    })


@login_required
def project_responses(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)

    submissions = (
        Submission.objects
        .filter(poll=poll)
        .select_related('user')
        .prefetch_related(
            'answers__selected_choices',
            'answers__question__choices',
        )
        .order_by('-created_at')
    )
    total_submissions = submissions.count()

    has_test_questions = poll.questions.filter(is_test_question=True).exists()

    rows = []
    questions = list(poll.questions.all())

    for sub in submissions:
        cells = []
        score = 0
        total = 0

        for q in questions:
            answer = None
            for ans in sub.answers.all():
                if ans.question_id == q.id:
                    answer = ans
                    break

            cell = ""

            if q.kind == Question.Kind.TEXT:
                if answer and answer.text_value.strip():
                    text = answer.text_value.strip()
                    cell = f"<div class='text-gray-800'>{text}</div>"
                else:
                    cell = '<span class="text-gray-400 text-sm">—</span>'
                cells.append(cell)

            elif q.kind in [Question.Kind.SINGLE, Question.Kind.MULTI]:
                selected_texts = []
                is_correct = False

                if answer and answer.selected_choices.exists():
                    # ✅ Используем `.text`, потому что в модели Choice поле называется `text`
                    for choice in answer.selected_choices.all():
                        selected_texts.append(choice.text)

                    if q.is_test_question:
                        total += 1
                        if answer.is_correct:
                            score += 1
                            is_correct = True

                if selected_texts:
                    text = ", ".join(selected_texts)
                    if q.is_test_question:
                        icon = "✅" if is_correct else "❌"
                        bg_class = "bg-green-50 text-green-800" if is_correct else "bg-red-50 text-red-800"
                        cell = (
                            f'<span class="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium '
                            f'{bg_class}">'
                            f'{text} <span class="font-bold">{icon}</span></span>'
                        )
                    else:
                        cell = f'<span class="text-gray-800 text-sm">{text}</span>'
                else:
                    cell = '<span class="text-gray-400 text-sm">—</span>'

                cells.append(cell)

        score_color = "#28a745" if score == total and total > 0 else "#dc3545" if total > 0 else "#6c757d"

        rows.append({
            'username': sub.user.get_full_name() or sub.user.username if sub.user else 'Аноним',
            'created_at': sub.created_at,
            'score': score,
            'total': total,
            'score_color': score_color,
            'cells': cells,
        })

    return render(request, 'dashboard/project_responses.html', {
        'poll': poll,
        'rows': rows,
        'has_test_questions': has_test_questions,
        'total_submissions': total_submissions,
    })