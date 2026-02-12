# polls/views/live.py
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from ..models import Answer, Poll, Question

@require_http_methods(["GET"])
def live_vote_count(request: HttpRequest) -> JsonResponse:
    code = request.GET.get("code", "").strip().upper()
    if not code:
        return JsonResponse({"ok": False, "error": "code required"}, status=400)

    poll = get_object_or_404(Poll, access_code=code)
    total = poll.submissions.count()

    questions_data = []

    questions = (
        poll.questions
        .prefetch_related("choices", "answers")
        .order_by("order")
    )

    for q in questions:
        if q.kind == Question.Kind.TEXT:
            count = q.answers.exclude(text_value="").count()
            questions_data.append({
                "kind": "TEXT",
                "text": q.text,
                "count": count,
            })
            continue

        choices = (
            q.choices
            .annotate(
                count=Count(
                    "answers",
                    filter=Q(answers__submission__poll=poll)
                )
            )
            .order_by("id")
        )

        questions_data.append({
            "kind": q.kind,
            "text": q.text,
            "choices": [
                {
                    "text": c.text,
                    "count": c.count,
                    "is_correct": c.is_correct,
                }
                for c in choices
            ],
        })

    return JsonResponse({
        "ok": True,
        "total_submissions": total,
        "questions": questions_data,
    })

