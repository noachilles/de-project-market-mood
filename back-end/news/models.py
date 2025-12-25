from django.db import models
from stocks.models import Stock

class News(models.Model):
    title = models.CharField(max_length=255)
    content_summary = models.TextField()          # LLM 요약 결과
    published_at = models.DateTimeField()
    sentiment_score = models.FloatField(null=True, blank=True)
    original_url = models.URLField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class NewsStockMapping(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("news", "stock")
