# polls/views/dashboard.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import PollForm
from ..models import Poll


@login_required
def project_list(request: HttpRequest) -> HttpResponse:
    polls = Poll.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "polls/project_list.html", {"polls": polls})


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
    poll = get_object_or_404(Poll, pk=poll_id, owner=request.user)
    questions = (
        poll.questions
        .order_by("order")
        .prefetch_related("choices")
    )

    return render(request, "dashboard/project_detail.html", {
        "poll": poll,
        "questions": questions,
    })
@login_required
def project_edit(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id, owner=request.user)
    if request.method == "POST":
        form = PollForm(request.POST, instance=poll)
        if form.is_valid():
            form.save()
            return redirect("polls:project_detail", poll_id=poll.id)
    else:
        form = PollForm(instance=poll)
    return render(request, "dashboard/poll_form.html", {"form": form, "title": "Редактировать", "poll": poll})


def project_delete(request, pk):
    poll = get_object_or_404(Poll, pk=pk)

    if request.method == "POST":
        title = poll.title
        poll.delete()

        # Если запрос от HTMX — возвращаем пустой ответ, чтобы удалить элемент
        if request.headers.get('HX-Request'):
            return HttpResponse('')

        # Если обычный POST (без HTMX) — редирект с сообщением
        messages.success(request, f'Опрос "{title}" удалён.')
        return redirect('polls:project_list')

    # Если GET — редирект (удаление только через POST)
    return redirect('polls:project_list')