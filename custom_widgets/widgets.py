from crispy_forms.layout import LayoutObject, Field
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import render_to_string
from django.forms.widgets import Select

from django import forms
from django.utils import translation
from django.db import DatabaseError
from django.utils.html import format_html


class TooltipSelect(Select):
    """A Select widget that adds title (tooltip) attributes to <option> elements."""

    def __init__(self, attrs=None, choices=(), tooltips=None):
        super().__init__(attrs=attrs, choices=choices)
        self.tooltips = tooltips or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        # Add the title attribute if a tooltip exists for this value
        tooltip = self.tooltips.get(value)
        if tooltip:
            option['attrs']['title'] = tooltip
        return option


class FieldWithButton(LayoutObject):
    """A Crispy Forms layout object that renders an input field with a button inline."""

    template = "core/widgets/field_with_button.html"

    def __init__(self, field, button, field_kwargs=None, **kwargs):
        self.field = field
        self.button = button
        self.field_kwargs = field_kwargs or {}
        self.attrs = kwargs

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        rendered_button = self.button.render(form, context, template_pack=template_pack, **kwargs)

        bound_field = form[self.field]
        rendered_input = bound_field.as_widget(attrs=self.field_kwargs)

        context.update({
            'rendered_input': rendered_input,
            'rendered_button': rendered_button,
            'field_label': form.fields[self.field].label,
            'field_name': self.field,
            'help_text': form.fields[self.field].help_text,
            'field_id': form[self.field].id_for_label,
        })
        return render_to_string(self.template, context.flatten())


class InstructionModelChoiceField(forms.ModelChoiceField):
    def __init__(
        self,
        *args,
        instruction_model=None,
        instruction_lookup=None,
        instruction_field="instructions",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.instruction_model = instruction_model
        self.instruction_lookup = instruction_lookup or {}
        self.instruction_field = instruction_field
        self._instruction_applied = False

    def apply_instruction_label(self):
        try:
            instruction = (
                self.instruction_model.objects
                .filter(**self.instruction_lookup)
                .only(
                    "instructions_en",
                    "instructions_fr",
                )
                .first()
            )
        except (LookupError, DatabaseError):
            return

        if not instruction:
            return

        language = translation.get_language()[:2]

        help_text = (
            instruction.instructions_fr
            if language == "fr" and instruction.instructions_fr
            else instruction.instructions_en
        )

        icon = format_html(
            '<span class="bi bi-question-circle me-1" '
            'title="{}" aria-label="{}"></span>',
            help_text,
            help_text,
        )
        self.label = format_html("{}{}", icon, self.label)