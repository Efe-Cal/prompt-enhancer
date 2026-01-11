from django.urls import path
from .views import EnhancePromptView, SavePromptView, ListSavedPromptsView

urlpatterns = [
    path('enhance/', EnhancePromptView.as_view(), name='enhance-prompt'),
    path('save/', SavePromptView.as_view(), name='save-prompt'),
    path('prompts/', ListSavedPromptsView.as_view(), name='list-prompts'),
]