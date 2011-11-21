from mobigame.models import Level, Question, Answer, Game, Player
from django.contrib import admin


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ['text', 'level']
    search_fields = ['text']


admin.site.register(Level)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Game)
admin.site.register(Player)
