

import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ✅ Перенесите функцию СНАРУЖИ классов, и не используйте lambda
def generate_access_code():
    """Генерирует уникальный 8-символьный код из заглавных букв и цифр."""
    chars = string.ascii_uppercase + string.digits
    for _ in range(10):  # Попробовать 10 раз
        code = "".join(secrets.choice(chars) for _ in range(8))
        if not Poll.objects.filter(access_code=code).exists():
            return code
    raise RuntimeError("Не удалось сгенерировать уникальный код доступа")


class Poll(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_polls",
        verbose_name="Владелец",
    )

    access_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        default=generate_access_code,  # ✅ Без lambda!
        verbose_name="Код доступа",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title




class Question(models.Model):
    class Kind(models.TextChoices):
        TEXT = "TEXT", "Текстовый ответ"
        SINGLE = "SINGLE", "Одиночный выбор"
        MULTI = "MULTI", "Множественный выбор"

    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Опрос",
    )
    text = models.CharField(
        max_length=500,
        verbose_name="Текст вопроса",
        help_text="Будет отображаться участникам опроса",
    )
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.TEXT,
        verbose_name="Тип вопроса",
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Порядок",
        help_text="Чем меньше число — тем выше вопрос (начинается с 1)",
    )
    is_test_question = models.BooleanField(
        default=False,
        verbose_name="Тестовый вопрос",
        help_text="Если включено — можно будет указать правильные варианты ответов.",
    )

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "order"],
                name="unique_order_per_poll"
            )
        ]
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self) -> str:
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Вопрос",
    )
    text = models.CharField(
        max_length=200,
        verbose_name="Текст варианта",
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Правильный ответ",
        help_text="Отметьте, если это правильный вариант (только для тестовых вопросов).",
    )

    class Meta:
        ordering = ["text"]
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def save(self, *args, **kwargs):
        # ⚠️ НЕТ self.full_clean(), НЕТ clean() — просто сохраняем
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.text


class Submission(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Опрос",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poll_submissions",
        verbose_name="Пользователь",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    # Результаты (если опрос — тест)
    score = models.PositiveIntegerField(default=0, verbose_name="Набрано баллов")
    total = models.PositiveIntegerField(default=0, verbose_name="Всего вопросов с проверкой")

    class Meta:
        verbose_name = "Ответ участника"
        verbose_name_plural = "Ответы участников"
        ordering = ["-created_at"]

    def calculate_score(self):
        """Пересчитывает и сохраняет количество правильных ответов."""
        correct = 0
        total = 0

        for answer in self.answers.select_related("question").prefetch_related("selected_choices"):
            if not answer.question.is_test_question:
                continue
            if answer.question.kind == Question.Kind.TEXT:
                continue

            total += 1
            if answer.is_correct is True:
                correct += 1

        self.score = correct
        self.total = total
        self.save(update_fields=["score", "total"])

    def __str__(self) -> str:
        user = self.user.get_full_name() if self.user else "Аноним"
        return f"{user} — {self.poll.title}"


class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Ответ на опрос",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос",
    )
    text_value = models.TextField(blank=True, verbose_name="Текстовый ответ")
    selected_choices = models.ManyToManyField(
        Choice,
        blank=True,
        through="AnswerChoice",
        related_name="answers",
        verbose_name="Выбранные варианты",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_submission_question"
            )
        ]
        verbose_name = "Ответ на вопрос"
        verbose_name_plural = "Ответы на вопросы"

    @property
    def is_correct(self) -> bool | None:
        """
        Возвращает:
        - True — если ответ правильный
        - False — если неправильный
        - None — если вопрос не подлежит проверке
        """
        if not self.question.is_test_question:
            return None
        if self.question.kind == Question.Kind.TEXT:
            return None

        if self.question.kind == Question.Kind.SINGLE:
            selected = self.selected_choices.first()
            correct = self.question.choices.filter(is_correct=True).first()
            return selected == correct

        if self.question.kind == Question.Kind.MULTI:
            selected_ids = set(self.selected_choices.values_list("id", flat=True))
            correct_ids = set(self.question.choices.filter(is_correct=True).values_list("id", flat=True))
            return selected_ids == correct_ids and bool(correct_ids)

        return None

    def __str__(self) -> str:
        q = self.question.text[:40]
        if self.text_value:
            return f"Текст: {self.text_value[:50]}..."
        choices = ", ".join(c.text for c in self.selected_choices.all())
        return f"Выбор: {choices or '(не выбрано)'}"


class AnswerChoice(models.Model):
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="selected_options",
        verbose_name="Ответ",
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="used_in",
        verbose_name="Вариант",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["answer", "choice"],
                name="unique_answer_choice"
            )
        ]
        verbose_name = "Выбранный вариант"
        verbose_name_plural = "Выбранные варианты"

    def __str__(self) -> str:
        return f"{self.answer} → {self.choice}"


