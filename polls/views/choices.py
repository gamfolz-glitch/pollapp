# polls/views/choices.py
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ChoiceForm
from ..models import Choice, Poll, Question


@login_required
def choice_new(request: HttpRequest, poll_id: int, question_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)
    question = get_object_or_404(Question, id=question_id, poll=poll)

    if request.method == "POST":
        form = ChoiceForm(request.POST, question=question)  # ✅ ВАЖНО
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question
            choice.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = ChoiceForm(question=question)  # ✅ И ТУТ ТОЖЕ

    return render(
        request,
        "dashboard/choice_form.html",
        {
            "form": form,
            "poll": poll,
            "question": question,
            "title": "Новый вариант",
        },
    )
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
    return render(request, "dashboard/choice_delete.html", {
        "poll": poll, "question": question, "choice": choice
    })