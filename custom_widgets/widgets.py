from crispy_forms.layout import LayoutObject, Field
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import render_to_string
from django.forms.widgets import Select


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