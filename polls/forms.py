from django import forms
from .models import Poll, Question, Choice


class PollForm(forms.ModelForm):
    """
    Форма для создания и редактирования опроса.
    Поля: название, описание.
    """

    class Meta:
        model = Poll
        fields = ["title", "description", "allow_multiple_submissions", "time_limit_minutes"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Опрос по Python",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Краткое описание опроса (необязательно)",
                }
            ),
            "allow_multiple_submissions": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        "time_limit_minutes": forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например: 5",
                "min": "1",
            }
        ),
        }
        labels = {
            "time_limit_minutes": "Ограничение времени (минуты)",
        }
        help_texts = {
            "time_limit_minutes": "Количество минут на прохождение опроса. Например: 5. Оставьте пустым — ограничения нет.",
        }

class QuestionForm(forms.ModelForm):
    """
    Форма для создания и редактирования вопроса.
    Поля: текст, тип, признак тестового вопроса.
    """

    is_test_question = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="🧪 Тестовый вопрос",
        help_text="Если включено — можно будет указать правильные варианты ответов.",
    )

    class Meta:
        model = Question
        fields = ["text", "kind", "is_test_question"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Введите текст вопроса",
                }
            ),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }
        labels = {
            "text": "Текст вопроса",
            "kind": "Тип вопроса",
        }
        help_texts = {
            "text": "Будет отображаться участникам опроса.",
            "kind": "Выберите тип ответа: текст, один выбор или несколько.",
        }





class ChoiceForm(forms.ModelForm):
    """
    Форма для создания и редактирования варианта ответа.
    """

    class Meta:
        model = Choice
        fields = ["text", "is_correct"]

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop("question", None)
        if self.question is None:
            raise ValueError("ChoiceForm требует передать 'question' при инициализации.")

        super().__init__(*args, **kwargs)

        self.fields["is_correct"].label = "✅ Правильный ответ"
        self.fields["is_correct"].help_text = (
            "Отметьте, если это правильный вариант (только для тестовых вопросов)"
        )

        # Если вопрос не тестовый — убираем поле полностью
        if not self.question.is_test_question:
            self.fields.pop("is_correct", None)

    def clean_is_correct(self):
        """
        Валидация чекбокса 'Правильный ответ'.
        Вызывается ТОЛЬКО если поле есть в форме.
        """
        # ЯВНАЯ проверка (если чекбокс не отмечен)
        is_correct = self.cleaned_data.get("is_correct", False)

        # Если не отмечен — всё ок
        if not is_correct:
            return is_correct

        # 🔒 Доп. защита (на случай ручной подмены POST)
        if not self.question.is_test_question:
            raise forms.ValidationError(
                "Нельзя отметить вариант как правильный — вопрос не тестовый."
            )

        # 🔒 Логика для SINGLE
        if self.question.kind == Question.Kind.SINGLE:
            qs = self.question.choices.filter(is_correct=True)

            # если редактируем — исключаем текущий вариант
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Для вопроса с одиночным выбором может быть только один правильный вариант. "
                    "Сначала снимите отметку с другого варианта."
                )

        return is_correct

    def save(self, commit=True):
        """
        Сохраняем вариант и привязываем его к вопросу.
        """
        choice = super().save(commit=False)
        choice.question = self.question
        if commit:
            choice.save()
        return choice