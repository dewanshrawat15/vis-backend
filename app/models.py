from django.db import models

# Create your models here.

class UserConsent(models.Model):
    consent_start = models.DateTimeField()
    consent_end = models.DateTimeField()
    customer_id = models.CharField(max_length = 24)
    # fi_date_range_from = models.DateTimeField()
    # fi_date_range_to = models.DateTimeField()

    consent_id = models.CharField(max_length = 72)
    is_active = models.BooleanField(default = False)

    def __str__(self):
        return self.customer_id