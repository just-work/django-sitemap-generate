from django.db import models


class Video(models.Model):
    def get_absolute_url(self):
        return f'/videos/{self.pk}/'


class Article(models.Model):
    def get_absolute_url(self):
        return f'/articles/{self.pk}'
