from django.contrib import admin

from app.models import Client, Appointment


class ClientAdmin(admin.ModelAdmin):
    list_display = ('telegram_chat_id', 'name', 'surname', 'phone')
    list_filter = ('telegram_chat_id', 'name', 'surname')
    search_fields = ['telegram_chat_id', 'name', 'surname', 'phone']


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'client_name', 'client_surname',  'date', 'time', 'pet_type')
    list_filter = ('date', 'time', 'pet_type')
    search_fields = ['client__name', 'client__surname', 'client__phone', 'date', 'time', 'pet_type']

    def client_name(self, obj):
        return obj.client.name

    def client_surname(self, obj):
        return obj.client.surname

    client_name.admin_order_field = 'client__name'
    client_surname.admin_order_field = 'client__surname'


admin.site.register(Client, ClientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
