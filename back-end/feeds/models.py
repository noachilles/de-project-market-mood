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

    # 3. 분석 결과 (Flink/Spark가 채워넣을 곳)
    sentiment_score = models.FloatField(null=True, blank=True, verbose_name="감정 점수")
    # 예: "HBM, 반도체, 실적" (분석된 키워드 저장)
    topics = models.JSONField(null=True, blank=True, verbose_name="주요 토픽") 

    class Meta:
        db_table = 'news'
        ordering = ['-published_at'] # 최신순 정렬

    def __str__(self):
        return self.title