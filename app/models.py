from django.db import models


class Client(models.Model):
    telegram_chat_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)


class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, to_field='telegram_chat_id')
    date = models.DateField(default=None, null=True)
    time = models.TimeField(default=None, null=True)
    pet_type = models.CharField(max_length=255)
