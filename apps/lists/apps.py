from django.apps import AppConfig

class ListsConfig(AppConfig):
    name = 'apps.lists'

    def ready(self):
        import apps.lists.nltk_setup
