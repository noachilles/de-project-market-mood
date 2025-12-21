from django.db import models

class Stock(models.Model):
    stock_code = models.CharField(max_length=10, primary_key=True)
    stock_name = models.CharField(max_length=50)
    sector = models.CharField(max_length=50, null=True, blank=True)
    market_type = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.stock_name}({self.stock_code})"


class StockPrice(models.Model):
    time = models.DateTimeField()
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, db_index=True)

    open = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    low = models.FloatField(null=True, blank=True)
    close = models.FloatField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "time"], name="uq_stockprice_stock_time")
        ]
        indexes = [
            models.Index(fields=["stock", "time"], name="idx_stockprice_stock_time"),
        ]
