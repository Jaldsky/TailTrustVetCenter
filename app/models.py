from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    telegram_chat_id = models.IntegerField(unique=True)


class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    appointment_datetime = models.DateTimeField()
    animal_type = models.CharField(max_length=255)
