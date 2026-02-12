from django.contrib import admin
from .models import Poll, Question, Choice, Submission, Answer


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created_at", "access_code"]
    list_filter = ["owner", "created_at"]
    search_fields = ["title", "description", "access_code"]
    readonly_fields = ["created_at", "access_code"]
    ordering = ["-created_at"]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    fields = ["text", "is_correct"]
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответов"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    def question_number(self, obj):
        return obj.order
    question_number.short_description = "№"
    question_number.admin_order_field = "order"

    list_display = ["question_number", "order", "text", "kind", "is_test_question", "poll"]
    list_filter = ["poll", "kind", "is_test_question"]
    search_fields = ["text"]
    list_editable = ["order"]  # Убрано: readonly_fields для order
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            if not obj.question.is_test_question:
                return ["text", "is_correct"]
            if obj.question.kind == Question.Kind.TEXT:
                return ["text", "is_correct"]
        return []

    def has_change_permission(self, request, obj=None):
        if obj and obj.question.kind == Question.Kind.TEXT:
            return False
        return super().has_change_permission(request, obj)

    list_display = ["text", "question", "is_correct"]
    list_filter = ["question__poll", "question", "is_correct"]
    search_fields = ["text"]


class AnswerInline(admin.TabularInline):
    def selected_choices_display(self, obj):
        if obj.question.kind in [Question.Kind.SINGLE, Question.Kind.MULTI]:
            return ", ".join([c.text for c in obj.selected_choices.all()])
        return "—"
    selected_choices_display.short_description = "Выбранные варианты"

    model = Answer
    extra = 0
    fields = ["text_value", "selected_choices_display"]
    readonly_fields = ["text_value", "selected_choices_display"]
    verbose_name = "Ответ на вопрос"
    verbose_name_plural = "Ответы на вопросы"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["poll", "user", "created_at", "score", "total"]
    list_filter = ["poll", "created_at", "user"]
    search_fields = ["poll__title", "user__username"]  # ✅ Исправлено
    readonly_fields = ["poll", "user", "created_at", "score", "total"]
    inlines = [AnswerInline]