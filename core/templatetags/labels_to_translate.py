from django.utils.translation import gettext as _

# Adding labels to this file ensures they are included in the .po files for translation. This is particularly
# important for labels that are not directly present in templates but are used elsewhere in the code, such as
# values that are loaded into lookup tables. Lookup tables often contain fields like 'name' and 'description' that need
# to be translated. While we typically provide labels in one language, adding them here allows them to be dynamically
# translated based on the user's language settings.
#
# Example usage:
# In a template, you might have a lookup table for 'leg status' with values like 'Expected', 'Submitted', etc.
# ```HTML
# <td>{{ leg.status }}</td>
# ```
#
# In this case, the 'status' field might contain values that are stored in a lookup table. By adding these values
# to this file, we ensure that they are included in the translation process and can be translated into different
# languages as needed. Then can be referenced in a template like this:
# ```HTML
# <td>{% trans leg.status %}</td>
# ```

# Todo: Develop a script that will automatically extract labels and descriptions from lookup tables to generate
#       this file automatically. And then will run the 'uv run manage.py makemessages' command to update
#       the .po files with the new labels and descriptions.

_("Expected")
_("Submitted")
_("Some data has been submitted. Follow up with the data provider and if all the data has been provided, mark it as received")
_("Lab")