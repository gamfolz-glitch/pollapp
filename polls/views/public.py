from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

import io
from ..models import Answer, Choice, Poll, Question, Submission


@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    latest_poll_list = Poll.objects.order_by("-created_at")[:10]
    return render(request, "polls/index.html", {"latest_poll_list": latest_poll_list})


@require_http_methods(["GET"])
def poll_code_redirect(request: HttpRequest) -> HttpResponse:
    code = (request.GET.get("code") or "").strip().upper()
    if not code:
        return redirect("/")
    return redirect(reverse("polls:poll_public", kwargs={"access_code": code}))


@require_http_methods(["GET", "POST"])
def poll_public(request: HttpRequest, access_code: str) -> HttpResponse:
    poll = get_object_or_404(Poll, access_code=access_code)
    questions = poll.questions.prefetch_related("choices").order_by("order", "id")

    # ───── идентификация ─────
    user = request.user if request.user.is_authenticated else None

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # ───── ограничение повторного прохождения (GET + POST) ─────
    if not poll.allow_multiple_submissions:
        if user:
            exists = Submission.objects.filter(poll=poll, user=user).exists()
        else:
            exists = Submission.objects.filter(
                poll=poll,
                user__isnull=True,
                session_key=session_key,
            ).exists()

        if exists:
            return render(
                request,
                "polls/poll_already_submitted.html",
                {"poll": poll},
            )

    # ✅ Стартуем таймер, если есть ограничение
    if poll.has_time_limit:
        timer_key = f"poll_start_time_{poll.id}"
        if timer_key not in request.session:
            request.session[timer_key] = timezone.now().timestamp()
            request.session.save()

    # ───── POST ─────
    if request.method == "POST":
        # ✅ Проверка времени (если ограничение есть)
        if poll.has_time_limit:
            timer_key = f"poll_start_time_{poll.id}"
            start_time = request.session.get(timer_key)
            if not start_time:
                return render(request, "polls/poll_timeout.html", {
                    "poll": poll,
                    "error": "Время сессии утеряно. Попробуйте начать заново."
                })

            elapsed = timezone.now().timestamp() - start_time
            if elapsed > poll.time_limit_in_seconds:
                return render(request, "polls/poll_timeout.html", {
                    "poll": poll,
                    "elapsed": int(elapsed / 60),
                    "limit": poll.time_limit_minutes,
                })

        # Валидация ответов
        answers_data = []
        errors = []

        for q in questions:
            field_name = f"q_{q.id}"
            if q.kind == Question.Kind.TEXT:
                text_value = (request.POST.get(field_name) or "").strip()
                if not text_value:
                    errors.append({"question_id": q.id, "message": "Введите ответ"})
                else:
                    answers_data.append(("TEXT", q, text_value))

            elif q.kind == Question.Kind.SINGLE:
                choice_id = request.POST.get(field_name)
                if not choice_id or not choice_id.isdigit():
                    errors.append({"question_id": q.id, "message": "Выберите один вариант"})
                else:
                    try:
                        choice = Choice.objects.get(id=int(choice_id), question=q)
                        answers_data.append(("SINGLE", q, choice))
                    except Choice.DoesNotExist:
                        errors.append({"question_id": q.id, "message": "Некорректный вариант"})

            elif q.kind == Question.Kind.MULTI:
                choice_ids = request.POST.getlist(field_name)
                if not choice_ids:
                    errors.append({"question_id": q.id, "message": "Выберите хотя бы один"})
                else:
                    choices = list(Choice.objects.filter(id__in=choice_ids, question=q))
                    if not choices:
                        errors.append({"question_id": q.id, "message": "Некорректные варианты"})
                    else:
                        answers_data.append(("MULTI", q, choices))

        if errors:
            return render(
                request,
                "polls/poll_public.html",
                {
                    "poll": poll,
                    "questions": questions,
                    "errors": errors,
                },
            )

        # Сохранение
        with transaction.atomic():
            submission = Submission.objects.create(
                poll=poll,
                user=user,
                session_key=session_key,
            )

            for kind, q, value in answers_data:
                if kind == "TEXT":
                    Answer.objects.create(
                        submission=submission,
                        question=q,
                        text_value=value,
                    )
                elif kind == "SINGLE":
                    answer = Answer.objects.create(submission=submission, question=q)
                    answer.selected_choices.add(value)
                elif kind == "MULTI":
                    answer = Answer.objects.create(submission=submission, question=q)
                    answer.selected_choices.set(value)

            submission.calculate_score()

        return redirect("polls:poll_thanks", access_code=access_code)

    # ───── GET: отображение формы ─────
    timer_key = f"poll_start_time_{poll.id}"
    time_left = None
    if poll.has_time_limit and timer_key in request.session:
        start_time = request.session[timer_key]
        elapsed = timezone.now().timestamp() - start_time
        time_left = max(0, poll.time_limit_in_seconds - int(elapsed))

    return render(
        request,
        "polls/poll_public.html",
        {
            "poll": poll,
            "questions": questions,
            "time_left": time_left,
        },
    )


@require_http_methods(["GET"])
def poll_thanks(request: HttpRequest, access_code: str) -> HttpResponse:
    poll = get_object_or_404(Poll, access_code=access_code)
    user = request.user if request.user.is_authenticated else None
    submission = Submission.objects.filter(poll=poll, user=user).order_by("-created_at").first()

    if not submission:
        return redirect("polls:poll_public", access_code=access_code)

    has_test_questions = poll.questions.filter(is_test_question=True).exists()
    answers_data = []

    if has_test_questions:
        for q in poll.questions.order_by("order"):
            answer = submission.answers.filter(question=q).first()
            given_text = answer.text_value if answer else ""
            given_choices = list(answer.selected_choices.all()) if answer else []
            correct_choices = list(q.choices.filter(is_correct=True)) if q.is_test_question else []

            answers_data.append({
                "question": q,
                "given_text": given_text,
                "given_choices": given_choices,
                "correct_choices": correct_choices,
                "is_correct": answer.is_correct if answer else None,
            })

    return render(request, "polls/poll_thanks.html", {
        "poll": poll,
        "submission": submission,
        "has_test_questions": has_test_questions,
        "answers_data": answers_data,
    })


@require_http_methods(["GET"])
def poll_qr_page(request: HttpRequest, access_code: str) -> HttpResponse:
    poll = get_object_or_404(Poll, access_code=access_code)
    public_url = request.build_absolute_uri(reverse("polls:poll_public", kwargs={"access_code": access_code}))
    return render(request, "polls/poll_qr.html", {"poll": poll, "public_url": public_url})


@require_http_methods(["GET"])
def poll_qr_png(request: HttpRequest, access_code: str) -> HttpResponse:
    try:
        import qrcode
    except ImportError:
        return HttpResponse("qrcode не установлен. Выполните: pip install qrcode[pil]", status=500)

    poll = get_object_or_404(Poll, access_code=access_code)
    url = request.build_absolute_uri(reverse("polls:poll_public", kwargs={"access_code": access_code}))
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")