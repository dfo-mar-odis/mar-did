class MARDIDRouter:
    auth_apps = {
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "messages",
        "staticfiles",
    }

    default_models = {
        "core.groupprofiles",
        "core.fieldinstructions"
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.auth_apps:
            return "default"

        if model._meta.label_lower in self.default_models:
            return "default"

        return "core"

    def db_for_write(self, model, **hints):

        if model._meta.app_label in self.auth_apps:
            return "default"

        if model._meta.label_lower in self.default_models:
            return "default"

        return "core"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.auth_apps:
            return db == "default"

        if app_label == "core" and model_name and f"core.{model_name.lower()}" in self.default_models:
            return db == "default"

        return db == "core"
