# coding=utf-8

from django.contrib import admin
from django import forms
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render
from feedback.models import Person, Veranstaltung, Semester, Einstellung, \
    Mailvorlage, Kommentar, Tutor, BarcodeScanner, BarcodeScannEvent, BarcodeAllowedState
from feedback.models.base import Log
from feedback import forms


# def status_angelegt(modeladmin, request, queryset):
#     queryset.update(status=100)
#     for veranstaltung in queryset:
#         veranstaltung.log(True, False)
# status_angelegt.short_description = 'Status: angelegt'
#
#
# def status_gedruckt(modeladmin, request, queryset):
#     queryset.update(status=600)
#     for veranstaltung in queryset:
#         veranstaltung.log(True, False)
# status_gedruckt.short_description = 'Status: gedruckt'
#
#
# def status_versandt(modeladmin, request, queryset):
#     queryset.update(status=700)
#     for veranstaltung in queryset:
#         veranstaltung.log(True, False)
# status_versandt.short_description = 'Status: versandt'
#
#
# def status_boegen_eingegangen(modeladmin, request, queryset):
#     queryset.update(status=800)
#     for veranstaltung in queryset:
#         veranstaltung.log(True, False)
# status_boegen_eingegangen.short_description = 'Status: eingegangen'
#
#
# def status_boegen_gescannt(modeladmin, request, queryset):
#     queryset.update(status=900)
#     for veranstaltung in queryset:
#         veranstaltung.log(True, False)
# status_boegen_gescannt.short_description = 'Status: gescannt'

class PersonAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email')
    search_fields = ['vorname', 'nachname', 'email', ]


class LogInline(admin.TabularInline):
    model = Log


class VeranstaltungAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stammdaten', {'fields':
                            ['typ', 'name', 'semester', 'status', 'lv_nr', 'grundstudium', 'evaluieren',
                             'veranstalter', 'link_veranstalter',
                             ]}),
        ('Bestellung', {'fields': ['sprache', 'anzahl', 'verantwortlich', 'ergebnis_empfaenger', 'auswertungstermin',
                                   'freiefrage1', 'freiefrage2', 'kleingruppen', ]}),
    ]
    list_display = ('typ', 'name', 'semester', 'grundstudium', 'evaluieren', 'anzahl',
                    'sprache', 'status', 'veranstalter_list')
    list_display_links = ['name']
    list_filter = ('typ', 'semester', 'grundstudium', 'evaluieren', 'sprache')
    search_fields = ['name']
    filter_horizontal = ('veranstalter', 'ergebnis_empfaenger')  # @see http://stackoverflow.com/a/5386871
    readonly_fields = ('link_veranstalter',)
    inlines = [LogInline, ]


class VeranstaltungStatus(Veranstaltung):
    class Meta:
        verbose_name = 'Status der Veranstaltung'
        verbose_name_plural = 'Status der Veranstaltungen'
        proxy = True


def status_aendern(self, request, queryset):
    form = None

    if 'apply' in request.POST:
        form = forms.StatusAendernForm(request.POST)

        if form.is_valid():
            status = form.cleaned_data['status']

            queryset.update(status=status)
            for veranstaltung in queryset:
                veranstaltung.log(request.user)

            self.message_user(request, "Status erfolgreich geändert.")
            return HttpResponseRedirect(request.get_full_path())

    if not form:
        form = forms.StatusAendernForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

    return render(request, 'admin/status_aendern.html', {'veranstaltungen': queryset, 'tag_form': form}, )

status_aendern.short_description = "Status ändern"



class VeranstaltungStatusAdmin(admin.ModelAdmin):
    list_display = ('lv_nr', 'name', 'status')
    list_display_links = ['name']
    list_filter = ('lv_nr', 'name', 'status')
    search_fields = ['name']
    actions = [
        status_aendern,
        #status_angelegt, status_gedruckt, status_versandt, status_boegen_eingegangen, status_boegen_gescannt
    ]


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'sichtbarkeit', 'fragebogen')
    list_filter = ('sichtbarkeit', 'fragebogen')
    ordering = ('-semester',)


class EinstellungAdmin(admin.ModelAdmin):
    list_display = ('name', 'wert')
    list_editable = ('wert',)


class MailvorlageAdmin(admin.ModelAdmin):
    list_display = ('subject',)


class KommentarAdmin(admin.ModelAdmin):
    list_display = ('typ', 'name', 'semester', 'autor')
    list_display_links = ('name',)


class TutorAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stammdaten', {'fields':
                            ['vorname', 'nachname', 'email',
                             ]}),
        ('Lehrveranstaltung', {'fields':
                                   ['veranstaltung', 'nummer', 'anmerkung'
                                    ]}),
    ]
    list_display = ('vorname', 'nachname', 'nummer', 'veranstaltung')
    search_fields = ('vorname', 'nachname')
    ordering = ('veranstaltung', 'nummer')

    def render_change_form(self, request, context, *args, **kwargs):
        # Limit Auswahl zum aktuellen Semester
        context['adminform'].form.fields['veranstaltung'].queryset = Veranstaltung.objects.filter(
            semester=Semester.current())
        return super(TutorAdmin, self).render_change_form(request, context, args, kwargs)


class BarcodeScannEventAdmin(admin.ModelAdmin):
    list_display = ('veranstaltung', 'timestamp',)
    readonly_fields = ('veranstaltung', 'timestamp',)


class BarcodeAllowedStateInline(admin.TabularInline):
    model = BarcodeAllowedState


class BarcodeScannerAdmin(admin.ModelAdmin):
    inlines = [
        BarcodeAllowedStateInline,
    ]
    list_display = ('token', 'description')


admin.site.register(Person, PersonAdmin)
admin.site.register(Veranstaltung, VeranstaltungAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Einstellung, EinstellungAdmin)
admin.site.register(Mailvorlage, MailvorlageAdmin)
admin.site.register(Kommentar, KommentarAdmin)
admin.site.register(Tutor, TutorAdmin)
admin.site.register(BarcodeScannEvent, BarcodeScannEventAdmin)
admin.site.register(BarcodeScanner, BarcodeScannerAdmin)
admin.site.register(VeranstaltungStatus, VeranstaltungStatusAdmin)
