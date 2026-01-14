from rest_framework import serializers



class EnhancePromptRequestSerializer(serializers.Serializer):
    task = serializers.CharField(required=True)
    lazy_prompt = serializers.CharField(required=True)
    use_web_search = serializers.BooleanField(required=False, default=False)
    additional_context_query = serializers.CharField(required=False, allow_blank=True, default="")


class EnhancePromptResponseSerializer(serializers.Serializer):
    enhancedPrompt = serializers.CharField()
    
class SavePromptSerializer(serializers.Serializer):
    task = serializers.CharField(required=True)
    lazy_prompt = serializers.CharField(required=True)
    enhanced_prompt = serializers.CharField(required=True)