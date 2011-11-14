from mobigame.models import Level, Question, Answer
from django.contrib import admin


class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 2


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


admin.site.register(Level)
admin.site.register(Question, QuestionAdmin)
