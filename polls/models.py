"""
Модели приложения опросов.
Включают опрос, вопросы, варианты, ответы и подсчёт результатов.
"""

import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Max

def generate_access_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(8))
        if not Poll.objects.filter(access_code=code).exists():
            return code

class Poll(models.Model):
    title = models.CharField(_("Название"), max_length=200)
    description = models.TextField(_("Описание"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_polls",
        verbose_name=_("Владелец"),
    )
    access_code = models.CharField(
        _("Код доступа"),
        max_length=8,
        unique=True,
        db_index=True,
        default=generate_access_code,
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    allow_multiple_submissions = models.BooleanField(
        _("Разрешить повторное прохождение"),
        default=False,
        help_text=_(
            "Если выключено — пользователь или аноним может пройти опрос только один раз."
        ),
    )

    time_limit_minutes = models.PositiveIntegerField(
        _("Ограничение времени (минуты)"),
        null=True,
        blank=True,
        help_text=_(
            "Если указано — участник должен пройти опрос за указанное количество минут. Оставьте пустым — нет ограничения.")
    )

    class Meta:
        verbose_name = _("Опрос")
        verbose_name_plural = _("Опросы")
        ordering = ["-created_at"]

    @property
    def has_time_limit(self) -> bool:
        return bool(self.time_limit_minutes)

    @property
    def time_limit_in_seconds(self) -> int:
        return self.time_limit_minutes * 60 if self.has_time_limit else 0

    def get_time_limit_display(self) -> str:
        return f"{self.time_limit_minutes} мин" if self.has_time_limit else "Без ограничения"

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"<Poll id={self.id} title='{self.title}' access_code='{self.access_code}'>"



class Question(models.Model):
    class Kind(models.TextChoices):
        TEXT = "TEXT", _("Текстовый ответ")
        SINGLE = "SINGLE", _("Одиночный выбор")
        MULTI = "MULTI", _("Множественный выбор")

    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("Опрос"),
    )
    text = models.CharField(
        _("Текст вопроса"),
        max_length=500,
        help_text=_("Будет отображаться участникам опроса"),
    )
    kind = models.CharField(
        _("Тип вопроса"),
        max_length=10,
        choices=Kind.choices,
        default=Kind.TEXT,
    )
    order = models.PositiveIntegerField(
        _("Порядок"),
        default=1,
        help_text=_("Чем меньше число — тем выше вопрос (начинается с 1)"),
    )
    is_test_question = models.BooleanField(
        _("Тестовый вопрос"),
        default=False,
        help_text=_("Если включено — можно будет указать правильные варианты ответов."),
    )

    class Meta:
        verbose_name = _("Вопрос")
        verbose_name_plural = _("Вопросы")
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "order"],
                name="unique_order_per_poll"
            )
        ]
    def clean(self):
        super().clean()
        if self.kind == Question.Kind.TEXT and self.is_test_question:
            raise ValidationError(_("Текстовые вопросы не могут быть тестовыми (нельзя проверять ответы)."))

    def save(self, *args, **kwargs):
        # Вызываем валидацию только если явно передано `validate=True`
        validate = kwargs.pop("validate", True)
        if validate:
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"<Question id={self.id} text='{self.text[:30]}...' poll_id={self.poll_id}>"

    @classmethod
    def next_order_for_poll(cls, poll):
        """
        Возвращает следующий порядковый номер для вопроса в опросе.
        """
        max_order = cls.objects.filter(poll=poll).aggregate(
            max_order=Max('order')
        )['max_order']
        return (max_order or 0) + 1

class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name=_("Вопрос"),
    )
    text = models.CharField(_("Текст варианта"), max_length=200)
    is_correct = models.BooleanField(
        _("Правильный ответ"),
        default=False,
        help_text=_("Отметьте, если это правильный вариант (только для тестовых вопросов)."),
    )
    class Meta:
        verbose_name = _("Вариант ответа")
        verbose_name_plural = _("Варианты ответов")
        ordering = ["text"]

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"<Choice id={self.id} text='{self.text[:30]}' is_correct={self.is_correct}>"

    def clean(self):
        super().clean()

        # ⚠️ если вопрос ещё не установлен — не валидируем
        if not self.question_id:
            return

        if self.is_correct and not self.question.is_test_question:
            raise ValidationError(
                {"is_correct": _("Нельзя пометить вариант как правильный, если вопрос не тестовый.")}
            )

        if self.is_correct and self.question.kind == Question.Kind.TEXT:
            raise ValidationError(
                {"is_correct": _("Нельзя указывать правильный ответ для текстового вопроса.")}
            )



class Submission(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Опрос"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="poll_submissions",
        verbose_name=_("Пользователь"),
    )

    created_at = models.DateTimeField(_("Дата отправки"), auto_now_add=True)
    score = models.PositiveIntegerField(_("Набрано баллов"), default=0)
    total = models.PositiveIntegerField(_("Всего вопросов с проверкой"), default=0)

    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Ключ сессии"),
    )

    class Meta:
        verbose_name = _("Ответ участника")
        verbose_name_plural = _("Ответы участников")
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
        user = self.user.get_full_name() if self.user else _("Аноним")
        return f"{user} — {self.poll.title}"

    def __repr__(self) -> str:
        return f"<Submission id={self.id} user_id={self.user_id} poll_id={self.poll_id}>"



class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Ответ на опрос"),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name=_("Вопрос"),
    )
    text_value = models.TextField(_("Текстовый ответ"), blank=True)
    selected_choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name="answers",
        verbose_name=_("Выбранные варианты"),
    )

    class Meta:
        verbose_name = _("Ответ на вопрос")
        verbose_name_plural = _("Ответы на вопросы")
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_submission_question"
            )
        ]

    @property
    def is_correct(self) -> bool | None:
        """
        Проверяет, правильный ли ответ.
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

    def __repr__(self) -> str:
        return f"<Answer id={self.id} submission_id={self.submission_id} question_id={self.question_id}>"
