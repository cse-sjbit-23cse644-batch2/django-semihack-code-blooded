from django.contrib import admin
from .models import Event, Participant


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'participant_count']

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'event', 'attended', 'score', 'level_display', 'certificate_id', 'registered_at']
    list_filter = ['event', 'attended']
    search_fields = ['name', 'email']
    readonly_fields = ['certificate_id', 'qr_code', 'registered_at']

    def level_display(self, obj):
        return obj.level or '—'
    level_display.short_description = 'Level'
