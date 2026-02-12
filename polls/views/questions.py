# polls/views/questions.py
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import QuestionForm
from ..models import Poll, Question


@login_required
def question_new(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, id=poll_id, owner=request.user)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.poll = poll
            question.order = Question.next_order_for_poll(poll)
            question.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = QuestionForm()

    return render(
        request,
        "dashboard/question_form.html",
        {
            "form": form,
            "poll": poll,
            "title": "Новый вопрос",
        },
    )

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