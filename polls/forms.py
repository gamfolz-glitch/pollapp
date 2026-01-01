from django import forms
from .models import Poll, Question, Choice


class PollForm(forms.ModelForm):
    """
    Форма для создания и редактирования опроса.
    Поля: название, описание.
    """

    class Meta:
        model = Poll
        fields = ["title", "description"]
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
        }


class QuestionForm(forms.ModelForm):
    """
    Форма для создания и редактирования вопроса.
    Поля: текст, тип, порядок, признак тестового вопроса.
    """

    # Явно объявляем is_test_question, чтобы гарантировать обработку `False` при отсутствии в POST
    is_test_question = forms.BooleanField(
        required=False,  # ✅ Критически важно: если не отмечен — будет False, а не ошибка
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="🧪 Тестовый вопрос",
        help_text="Если включено — можно будет указать правильные варианты ответов."
    )

    class Meta:
        model = Question
        fields = ["text", "kind", "is_test_question", "order"]
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
            "order": "Порядок",
        }
        help_texts = {
            "text": "Будет отображаться участникам опроса.",
            "kind": "Выберите тип ответа: текст, один выбор или несколько.",
            "order": "Чем меньше число, тем выше вопрос в опросе. Начинается с 1.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем значение по умолчанию для порядка, если создаём новый вопрос
        if not self.instance.pk:
            self.fields["order"].initial = (
                self.fields["order"].initial or 1
            )




class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]

    def __init__(self, *args, **kwargs):
        # Получаем question и удаляем из kwargs, чтобы не передавать в super()
        self.question = kwargs.pop("question", None)
        super().__init__(*args, **kwargs)

        # Подписи
        self.fields["is_correct"].label = "✅ Правильный ответ"
        self.fields["is_correct"].help_text = "Отметьте, если это правильный вариант (только для тестовых вопросов)"

        # Скрываем is_correct, если вопрос не тестовый
        if self.question and not self.question.is_test_question:
            del self.fields["is_correct"]

    def clean(self):
        cleaned_data = super().clean()
        is_correct = cleaned_data.get("is_correct")

        # Используем self.question — он гарантированно есть, если передан при создании формы
        if is_correct and self.question and not self.question.is_test_question:
            raise forms.ValidationError(
                "Нельзя отметить вариант как правильный, если вопрос не является тестовым."
            )

        if is_correct and self.question:
            if self.question.kind == Question.Kind.SINGLE:
                existing = self.question.choices.filter(is_correct=True)
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise forms.ValidationError(
                        "Для одиночного выбора уже есть правильный ответ. Сначала снимите метку с другого варианта."
                    )
        return cleaned_data