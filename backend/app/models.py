from django.db import models

class AnalysisLog(models.Model):
    ana_id = models.AutoField(primary_key=True, db_column='ana_id')
    run_at = models.CharField(max_length=50, unique=True)
    lookback_days = models.IntegerField()

    class Meta:
        db_table = 'analysis_log'
        verbose_name_plural = 'Analysis Logs'

    def __str__(self):
        return f"Analysis {self.ana_id} at {self.run_at}"


class News(models.Model):
    django_id = models.AutoField(primary_key=True, db_column='django_id')
    analysis = models.ForeignKey(AnalysisLog, on_delete=models.CASCADE, related_name='news', db_column='ana_id')
    news_id = models.CharField(max_length=255, db_column='id')
    source = models.CharField(max_length=100)
    title = models.TextField()
    url = models.URLField(max_length=1024)
    published_date = models.CharField(max_length=50, blank=True, null=True)
    document_type = models.CharField(max_length=100, blank=True, null=True)
    summary = models.TextField(default='')
    content = models.TextField(default='')
    agencies = models.TextField(default='')  # Comma-separated list of agencies
    run_at = models.CharField(max_length=50)

    class Meta:
        db_table = 'news'
        unique_together = ('analysis', 'news_id')
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title


class Company(models.Model):
    django_id = models.AutoField(primary_key=True, db_column='django_id')
    analysis = models.ForeignKey(AnalysisLog, on_delete=models.CASCADE, related_name='companies', db_column='ana_id')
    ticker = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=100, blank=True, null=True)
    industry_code = models.CharField(max_length=100, blank=True, null=True)
    industry_name = models.CharField(max_length=255, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    rating = models.CharField(max_length=50, blank=True, null=True)
    thesis = models.TextField(default='')
    evidence = models.TextField(default='')  # Comma-separated or JSON string of evidence titles
    sector = models.CharField(max_length=255, blank=True, null=True)
    stock_industry = models.CharField(max_length=255, blank=True, null=True)
    related_industries = models.TextField(default='')  # Comma-separated list of industries
    run_at = models.CharField(max_length=50)

    class Meta:
        db_table = 'companies'
        unique_together = ('analysis', 'ticker')
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.ticker} - {self.name}"


class Industry(models.Model):
    django_id = models.AutoField(primary_key=True, db_column='django_id')
    analysis = models.ForeignKey(AnalysisLog, on_delete=models.CASCADE, related_name='industries', db_column='ana_id')
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    score = models.FloatField()
    momentum = models.FloatField(default=0.0)
    policy_count = models.IntegerField(default=0)
    positive_signals = models.IntegerField(default=0)
    risk_signals = models.IntegerField(default=0)
    key_drivers = models.TextField(default='')  # Comma-separated list of drivers
    evidence_policy_ids = models.TextField(default='')  # Comma-separated list of policy IDs

    class Meta:
        db_table = 'industries'
        unique_together = ('analysis', 'code')
        verbose_name_plural = 'Industries'

    def __str__(self):
        return self.name


class SubsidiaryMapping(models.Model):
    subsidiary_name = models.CharField(max_length=255, unique=True, verbose_name="子公司名稱 (小寫)")
    parent_company_name = models.CharField(max_length=255, verbose_name="母公司名稱")

    class Meta:
        db_table = 'subsidiary_mapping'
        verbose_name_plural = 'Subsidiary Mappings'

    def save(self, *args, **kwargs):
        self.subsidiary_name = self.subsidiary_name.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subsidiary_name} -> {self.parent_company_name}"


class MacroObservation(models.Model):
    django_id = models.AutoField(primary_key=True, db_column='django_id')
    category = models.CharField(max_length=50, db_index=True)
    metric_name = models.CharField(max_length=100, db_index=True)
    series_id = models.CharField(max_length=50)
    source = models.CharField(max_length=100)
    date = models.CharField(max_length=50)  # Standard date string 'YYYY-MM-DD'
    value = models.FloatField()
    fetched_at = models.CharField(max_length=50, default='')

    class Meta:
        db_table = 'macro_observations'
        verbose_name_plural = 'Macro Observations'
        unique_together = ('series_id', 'date')

    def __str__(self):
        return f"{self.metric_name} ({self.date}): {self.value}"


