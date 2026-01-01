from django.contrib import admin
from .models import Poll, Question, Choice, Submission, Answer



@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created_at", "access_code"]
    list_filter = ["owner", "created_at"]
    search_fields = ["title", "description", "access_code"]
    readonly_fields = ["created_at", "access_code"]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    fields = ["text", "is_correct"]
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответов"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    def question_number(self, obj):
        """Порядковый номер вопроса (начинается с 1)"""
        return obj.order
    question_number.short_description = "№"
    question_number.admin_order_field = "order"  # ← Позволяет сортировать по 'order'

    # ✅ Добавляем 'order' в list_display, но можно скрыть его через CSS или оставить (не страшно)
    list_display = ["question_number", "order", "text", "kind", "is_test_question", "poll"]
    list_filter = ["poll", "kind", "is_test_question"]
    search_fields = ["text"]
    list_editable = ["order"]  # ✅ Теперь 'order' есть в list_display
    readonly_fields = ["order"]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["text", "question", "is_correct"]
    list_filter = ["question__poll", "question", "is_correct"]
    search_fields = ["text"]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ["text_value", "selected_choices"]
    readonly_fields = ["text_value", "selected_choices"]
    verbose_name = "Ответ на вопрос"
    verbose_name_plural = "Ответы на вопросы"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["poll", "user", "created_at", "score", "total"]
    list_filter = ["poll", "created_at", "user"]
    search_fields = ["poll__title", "user__username"]
    readonly_fields = ["poll", "user", "created_at", "score", "total"]
    inlines = [AnswerInline]