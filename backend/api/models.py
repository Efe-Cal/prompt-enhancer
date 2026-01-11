from django.db import models

class SavedPrompt(models.Model):
    class Meta:
        verbose_name = "Saved Prompt"
        verbose_name_plural = "Saved Prompts"
        
    id = models.AutoField(primary_key=True)
    task = models.CharField(max_length=255, blank=True)
    lazy_prompt = models.TextField()
    enhanced_prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"Prompt for task: {self.task or '(Untitled)'} created at {self.created_at}"
