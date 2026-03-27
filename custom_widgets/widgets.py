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