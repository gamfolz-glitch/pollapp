from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Count, F, Max
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import ChoiceForm, PollForm, QuestionForm
from .models import Answer, Choice, Poll, Question, Submission


@dataclass
class FormError:
    question_id: int
    message: str


# ------------------------------------------------------------------------------
# PUB: Публичные вьюхи — прохождение опроса
# ------------------------------------------------------------------------------

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

    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        submission = Submission.objects.create(poll=poll, user=user)

        errors: list[FormError] = []

        for q in questions:
            field_name = f"q_{q.id}"

            if q.kind == Question.Kind.TEXT:
                text_value = (request.POST.get(field_name) or "").strip()
                if not text_value:
                    errors.append(FormError(q.id, "Введите ответ"))
                    continue
                Answer.objects.create(submission=submission, question=q, text_value=text_value)

            elif q.kind == Question.Kind.SINGLE:
                choice_id = request.POST.get(field_name)
                if not choice_id or not choice_id.isdigit():
                    errors.append(FormError(q.id, "Выберите один вариант"))
                    continue
                choice = get_object_or_404(Choice, id=int(choice_id), question=q)
                answer = Answer.objects.create(submission=submission, question=q)
                answer.selected_choices.add(choice)

            elif q.kind == Question.Kind.MULTI:
                choice_ids = request.POST.getlist(field_name)
                if not choice_ids:
                    errors.append(FormError(q.id, "Выберите хотя бы один"))
                    continue
                choices = Choice.objects.filter(id__in=choice_ids, question=q)
                if not choices:
                    errors.append(FormError(q.id, "Некорректные варианты"))
                    continue
                answer = Answer.objects.create(submission=submission, question=q)
                answer.selected_choices.set(choices)

        if not errors:
            submission.calculate_score()
            return redirect(reverse("polls:poll_thanks", kwargs={"access_code": access_code}))

        submission.delete()
        context = {"poll": poll, "questions": questions, "errors": errors}
        return render(request, "polls/poll_public.html", context)

    return render(request, "polls/poll_public.html", {"poll": poll, "questions": questions})


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


# ------------------------------------------------------------------------------
# ANALYTICS: Статистика и ответы (владелец)
# ------------------------------------------------------------------------------

@login_required
def project_stats(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    total = Submission.objects.filter(poll=poll).count()

    questions_stats = []
    for q in poll.questions.order_by("order"):
        if q.kind == Question.Kind.TEXT:
            answered = Answer.objects.filter(submission__poll=poll, question=q).exclude(text_value="").count()
            questions_stats.append({"kind": "TEXT", "text": q.text, "answered": answered})
            continue

        choices = (
            Choice.objects.filter(question=q)
            .annotate(count=Count("answers"))
            .order_by("id")
        )
        total_q = max(sum(c.count for c in choices), 1)
        questions_stats.append({
            "kind": q.kind,
            "text": q.text,
            "choices": [
                {"text": c.text, "count": c.count, "percent": round(c.count / total_q * 100, 1), "is_correct": c.is_correct}
                for c in choices
            ],
        })

    return render(request, "dashboard/project_stats.html", {
        "poll": poll,
        "total_submissions": total,
        "questions_stats": questions_stats,
    })


@login_required
def project_responses(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)

    user_filter = request.GET.get("user", "").strip()
    text_filter = request.GET.get("text", "").strip()

    submissions = Submission.objects.filter(poll=poll).select_related("user").prefetch_related(
        "answers__question", "answers__selected_choices"
    ).order_by("-created_at")

    if user_filter:
        submissions = submissions.filter(user__username__icontains=user_filter)

    # Поиск по текстовым ответам и вариантам
    if text_filter:
        answer_ids = set(
            Answer.objects.filter(
                submission__poll=poll,
                text_value__icontains=text_filter
            ).values_list("submission_id", flat=True)
        ) | set(
            Answer.objects.filter(
                submission__poll=poll,
                selected_choices__text__icontains=text_filter
            ).values_list("submission_id", flat=True)
        )
        if answer_ids:
            submissions = submissions.filter(id__in=answer_ids)
        else:
            submissions = submissions.none()

    questions = list(poll.questions.order_by("order"))
    has_test_questions = poll.questions.filter(is_test_question=True).exists()

    rows = []
    for s in submissions:
        row = {
            "username": s.user.get_full_name() or s.user.username if s.user else "Аноним",
            "created_at": s.created_at,
            "score": None,
            "total": None,
            "score_color": "#9E9E9E",
            "cells": [],
        }

        if has_test_questions and s.total > 0:
            row["score"] = s.score
            row["total"] = s.total
            row["score_color"] = "#4CAF50" if s.score == s.total else "#FF9800" if s.score > 0 else "#F44336"

        answers_dict = {a.question: a for a in s.answers.all()}
        for q in questions:
            answer = answers_dict.get(q)
            if not answer:
                row["cells"].append("—")
            elif q.kind == Question.Kind.TEXT:
                row["cells"].append(answer.text_value or "—")
            else:
                selected = [c.text for c in answer.selected_choices.all()]
                row["cells"].append(", ".join(selected) if selected else "—")

        rows.append(row)

    return render(request, "dashboard/project_responses_table.html", {
        "poll": poll,
        "has_test_questions": has_test_questions,
        "rows": rows,
        "questions": questions,
    })


# ------------------------------------------------------------------------------
# LIVE: Live-статистика
# ------------------------------------------------------------------------------

@require_http_methods(["GET"])
def live_vote_count(request: HttpRequest) -> JsonResponse:
    code = request.GET.get("code", "").strip()
    if not code:
        return JsonResponse({"ok": False, "error": "code required"}, status=400)

    poll = get_object_or_404(Poll, access_code=code)
    total = Submission.objects.filter(poll=poll).count()

    questions_data = []
    for q in poll.questions.order_by("order"):
        if q.kind == Question.Kind.TEXT:
            count = Answer.objects.filter(submission__poll=poll, question=q).exclude(text_value="").count()
            questions_data.append({"kind": "TEXT", "text": q.text, "count": count})
        else:
            choices = (
                Choice.objects.filter(question=q)
                .annotate(count=Count("answers"))
                .order_by("id")
            )
            questions_data.append({
                "kind": q.kind,
                "text": q.text,
                "choices": [{"text": c.text, "count": c.count, "is_correct": c.is_correct} for c in choices],
            })

    return JsonResponse({
        "ok": True,
        "total_submissions": total,
        "questions": questions_data,
    })


# ------------------------------------------------------------------------------
# DASHBOARD: Управление опросами
# ------------------------------------------------------------------------------

@login_required
def project_list(request: HttpRequest) -> HttpResponse:
    polls = Poll.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "dashboard/project_list.html", {"polls": polls})


@login_required
def project_new(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.owner = request.user
            poll.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = PollForm()
    return render(request, "dashboard/poll_form.html", {"form": form, "title": "Новый опрос"})


@login_required
def project_detail(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    return render(request, "dashboard/project_detail.html", {
        "poll": poll,
        "questions": poll.questions.order_by("order"),
    })


@login_required
def project_edit(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    if request.method == "POST":
        form = PollForm(request.POST, instance=poll)
        if form.is_valid():
            form.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = PollForm(instance=poll)
    return render(request, "dashboard/poll_form.html", {"form": form, "title": "Редактировать", "poll": poll})


@login_required
def project_delete(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    if request.method == "POST":
        poll.delete()
        return redirect("polls:project_list")
    return render(request, "dashboard/poll_delete.html", {"poll": poll})


# ------------------------------------------------------------------------------
# QUESTIONS: Управление вопросами
# ------------------------------------------------------------------------------

@login_required
def question_new(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.poll = poll
            question.order = (poll.questions.aggregate(Max('order'))['order__max'] or 0) + 1
            question.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = QuestionForm()
    return render(request, "dashboard/question_form.html", {"form": form, "poll": poll, "title": "Новый вопрос"})


@login_required
def question_edit(request: HttpRequest, poll_id: int, question_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = QuestionForm(instance=question)
    return render(request, "dashboard/question_form.html", {
        "form": form, "poll": poll, "question": question, "title": "Редактировать вопрос"
    })


@login_required
def question_delete(request: HttpRequest, poll_id: int, question_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)
    if request.method == "POST":
        question.delete()
        return redirect("polls:project_detail", poll_id=poll.id)
    return render(request, "dashboard/question_delete.html", {"poll": poll, "question": question})


# ------------------------------------------------------------------------------
# CHOICES: Управление вариантами
# ------------------------------------------------------------------------------

@login_required
def choice_new(request: HttpRequest, poll_id: int, question_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)
    if request.method == "POST":
        form = ChoiceForm(request.POST, question=question)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question
            choice.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = ChoiceForm(question=question)
    return render(request, "dashboard/choice_form.html", {
        "form": form, "poll": poll, "question": question, "title": "Новый вариант"
    })


@login_required
def choice_edit(request: HttpRequest, poll_id: int, question_id: int, choice_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)
    choice = get_object_or_404(Choice, id=choice_id, question=question)
    if request.method == "POST":
        form = ChoiceForm(request.POST, instance=choice, question=question)
        if form.is_valid():
            form.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = ChoiceForm(instance=choice, question=question)
    return render(request, "dashboard/choice_form.html", {
        "form": form, "poll": poll, "question": question, "choice": choice, "title": "Редактировать вариант"
    })


@login_required
def choice_delete(request: HttpRequest, poll_id: int, question_id: int, choice_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)
    choice = get_object_or_404(Choice, id=choice_id, question=question)
    if request.method == "POST":
        choice.delete()
        return redirect("polls:project_detail", poll_id=poll.id)
    return render(request, "dashboard/choice_delete.html", {"poll": poll, "question": question, "choice": choice})


# ------------------------------------------------------------------------------
# AUTH: Регистрация
# ------------------------------------------------------------------------------

def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("polls:project_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

@require_http_methods(["GET"])
@login_required
def question_correct_count(request, question_id):
    question = get_object_or_404(Question, id=question_id, poll__owner=request.user)
    count = question.choices.filter(is_correct=True).count()
    return JsonResponse({"count": count})