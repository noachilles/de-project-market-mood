from rest_framework import serializers

class NewsItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    source = serializers.CharField(allow_blank=True, required=False)
    title = serializers.CharField()
    link = serializers.CharField()
    published_at = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
