from django.db import models

class News(models.Model):
    # 1. 기본 정보 (RSS에서 획득)
    title = models.CharField(max_length=500, verbose_name="기사 제목")
    link = models.URLField(max_length=1000, unique=True, verbose_name="기사 링크")
    summary = models.TextField(blank=True, null=True, verbose_name="RSS 요약")
    published_at = models.DateTimeField(verbose_name="발행 일시")

    # 2. (필수 추가) 본문 데이터 (크롤링으로 획득)
    # CharField는 길이 제한이 있으므로, 제한 없는 TextField 사용
    content = models.TextField(blank=True, null=True, verbose_name="기사 본문 전체")

    summary = models.TextField(null=True, blank=True)         # 3줄 요약
    keywords = models.CharField(max_length=200, null=True, blank=True)
    related_symbols = models.CharField(max_length=200, null=True, blank=True) # "US:NVDA,KR:005930"
    source = models.CharField(max_length=50, null=True, blank=True)   # Google, MK 등
    sentiment = models.CharField(max_length=20, null=True, blank=True) # Positive/Negative
    reason = models.TextField(null=True, blank=True)          # 연결 이유
    
    class Meta:
        db_table = 'news'
        ordering = ['-published_at'] # 최신순 정렬

    def __str__(self):
        return self.title