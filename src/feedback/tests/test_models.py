# coding=utf-8

from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import now
from freezegun import freeze_time

from feedback.models import get_model, Semester, Person, Veranstaltung, Einstellung, Mailvorlage
from feedback.models.base import AlternativVorname, Log
from feedback.models import past_semester_orders
from feedback.models import ImportPerson, ImportCategory, ImportVeranstaltung, Kommentar
from feedback.models import Fragebogen2008, Fragebogen2009, Ergebnis2008, Ergebnis2009
from feedback.models import Fragebogen2012, Ergebnis2012
from feedback.tests.tools import get_veranstaltung



class InitTest(TestCase):
    def setUp(self):
        self.s = []
        self.s.append(Semester.objects.create(semester=20110, fragebogen='2008'))
        self.s.append(Semester.objects.create(semester=20115, fragebogen='2009'))
        self.s.append(Semester.objects.create(semester=20125, fragebogen='2012'))

    def test_get_model(self):
        self.assertEqual(get_model('Fragebogen', self.s[0]), Fragebogen2008)
        self.assertEqual(get_model('Fragebogen', self.s[1]), Fragebogen2009)
        self.assertEqual(get_model('Fragebogen', self.s[2]), Fragebogen2012)
        self.assertEqual(get_model('Ergebnis', self.s[0]), Ergebnis2008)
        self.assertEqual(get_model('Ergebnis', self.s[1]), Ergebnis2009)
        self.assertEqual(get_model('Ergebnis', self.s[2]), Ergebnis2012)


class pastOrdersTest(TestCase):
    def setUp(self):
        current_sem = Semester.objects.create(semester=20125, fragebogen='2012')
        past_sem = Semester.objects.create(semester=20115, fragebogen='2009')
        future_sem = Semester.objects.create(semester=20130, fragebogen='2012')

        self.default_params = {'typ': 'v', 'name': 'Stoning I',
                               'grundstudium': False, 'evaluieren': True}

        self.singleLV = Veranstaltung.objects.create(semester=current_sem, lv_nr='20-00-0021-lv', **self.default_params)

        self.lv = []
        self.lv.append(
            Veranstaltung.objects.create(semester=past_sem, lv_nr='20-00-0042-lv', anzahl=10, **self.default_params))
        self.lv.append(Veranstaltung.objects.create(semester=current_sem, lv_nr='20-00-0042-lv', **self.default_params))

        self.lv.append(Veranstaltung.objects.create(semester=past_sem, lv_nr='20-00-0043-lv', **self.default_params))
        self.lv.append(Veranstaltung.objects.create(semester=current_sem, lv_nr='20-00-0043-lv', **self.default_params))
        self.lv.append(
            Veranstaltung.objects.create(semester=future_sem, lv_nr='20-00-0043-lv', anzahl=10, **self.default_params))

        self.erg = []
        self.erg.append(Ergebnis2009.objects.create(veranstaltung=self.lv[0], anzahl=5,
                                                    v_gesamt=1, v_gesamt_count=2,
                                                    ue_gesamt=2, ue_gesamt_count=3,
                                                    v_feedbackpreis=3, v_feedbackpreis_count=4))

    def test_no_past(self):
        """Die Veranstaltung wird das erste mal gehalten"""
        result = past_semester_orders(self.singleLV)
        self.assertEqual(len(result), 0)
        self.assertEqual(past_semester_orders(self.singleLV), [],
                         'Die Liste sollte leer sein. Die Veranstaltung wird das erste mal angeboten.')

    def test_one_befor(self):
        """Die Veranstaltung wurde schonmal gehalten, es wurde bestellt und auch Ergebnisse geliefert"""
        result = past_semester_orders(self.lv[1])
        self.assertEqual(len(result), 1)

        expeted_dict = {'veranstaltung': self.lv[0], 'anzahl_bestellung': 10, 'anzahl_ruecklauf': 5}

        self.assertDictEqual(expeted_dict, result[0])

    def test_one_befor_current_ordert(self):
        """Für die aktuelle Veranstaltung wurde eine Bestellung aufgegeben.
        In der Vergangenheit gab es die Veranstaltung einmal."""
        self.lv[1].anzahl = 42
        self.lv[1].save()

        result = past_semester_orders(self.lv[1])
        self.assertEqual(len(result), 1)

        expeted_dict = {'veranstaltung': self.lv[0], 'anzahl_bestellung': 10, 'anzahl_ruecklauf': 5}

        self.assertDictEqual(expeted_dict, result[0])

    def test_not_exist(self):
        """Die Veranstaltung wurde schon einmal gehalten, es wurde jedoch nichts bestellt"""
        result = past_semester_orders(self.lv[3])
        self.assertEqual(len(result), 0)

    def test_no_result_exist(self):
        """Die Veranstaltung wurde gehalten, es wurde bestellt jedoch gibt es keine Ergebnisse"""
        self.lv[2].anzahl = 10
        self.lv[2].save()

        result = past_semester_orders(self.lv[3])

        self.assertEqual(len(result), 1)

        expeted_dict = {'veranstaltung': self.lv[2], 'anzahl_bestellung': 10, 'anzahl_ruecklauf': 0}

        self.assertDictEqual(expeted_dict, result[0])


class SemesterTest(TestCase):
    def setUp(self):
        self.ws = Semester.objects.create(semester=20115, fragebogen='test', sichtbarkeit='ADM')
        self.ss = Semester.objects.create(semester=20120, fragebogen='test', sichtbarkeit='ADM')

    def test_short(self):
        self.assertEqual(self.ws.short(), 'WS 2011/2012')
        self.assertEqual(self.ss.short(), 'SS 2012')

    def test_long(self):
        self.assertEqual(self.ws.long(), 'Wintersemester 2011/2012')
        self.assertEqual(self.ss.long(), 'Sommersemester 2012')

    def test_unicode(self):
        self.assertEqual(unicode(self.ws), 'Wintersemester 2011/2012')
        self.assertEqual(unicode(self.ss), 'Sommersemester 2012')

    def test_current(self):
        self.assertEqual(Semester.current(), self.ss)

    def test_is_unique(self):
        with self.assertRaises(IntegrityError):
            Semester.objects.create(semester=20115, fragebogen='foo', sichtbarkeit='ALL')


class PersonTest(TestCase):
    def setUp(self):
        self.p1 = Person.objects.create(vorname='Brian', nachname='Cohen')
        self.p2 = Person.objects.create(vorname='Bud', nachname='Spencer', email='x@y.z')
        self.p3 = Person.objects.create(vorname='Test', nachname='Tester', email='a@b.c', geschlecht='m')
        self.p4 = Person.objects.create(vorname='Test Zweitname', nachname='Tester')

        self.s1, self.v1 = get_veranstaltung('v')
        self.v1.veranstalter = [self.p1]

        self.s2 = Semester.objects.get_or_create(semester=20115, fragebogen='2009', sichtbarkeit='ADM')[0]
        default_params = {'semester': self.s2, 'grundstudium': False, 'evaluieren': True, 'lv_nr': '321' + 'v'}
        self.v2 = Veranstaltung.objects.create(typ='v', name='CMS', **default_params)
        self.v2.veranstalter = [self.p4]

    def test_full_name(self):
        self.assertEqual(self.p1.full_name(), 'Brian Cohen')

    def test_unicode(self):
        self.assertEqual(unicode(self.p1), 'Cohen, Brian')

    def test_create_from_import_person(self):
        ip = ImportPerson(vorname='Brian', nachname='Cohen')
        p = Person.create_from_import_person(ip)
        self.assertEqual(p, self.p1)

        ip.vorname = 'Eric'
        p = Person.create_from_import_person(ip)
        self.assertNotEqual(p, self.p1)

    def test_persons_to_edit(self):
        to_edit_persons = Person.persons_to_edit(semester=self.s1)
        self.assertEqual(to_edit_persons.count(), 1)
        self.assertTrue(to_edit_persons.filter(vorname='Brian').exists())

    def test_all_edited_persons(self):
        edited_persons = Person.all_edited_persons()
        self.assertEqual(edited_persons.count(), 1)
        self.assertTrue(edited_persons.filter(email='a@b.c', geschlecht='m').exists())

    def test_persons_with_similar_names(self):
        similar_persons = Person.persons_with_similar_names('Test', 'Tester')
        self.assertEqual(similar_persons.count(), 1)
        self.assertTrue(similar_persons.filter(vorname='Test').exists())

    def test_veranstaltungen(self):
        veranstaltungen = Person.veranstaltungen(self.p1)
        veranstalter_name = veranstaltungen.filter(veranstalter=self.p1)[0].veranstalter.get().full_name()
        self.assertEqual(veranstaltungen.count(), 1)
        self.assertEqual(self.p1.full_name(), veranstalter_name)

    def test_replace_veranstalter(self):
        # when
        Person.replace_veranstalter(self.p4, self.p3)

        # then
        self.assertFalse(Person.veranstaltungen(self.p4).exists())
        self.assertEqual(Person.veranstaltungen(self.p3).count(), 1)
        self.assertEqual(AlternativVorname.objects.get().vorname, self.p4.vorname)
        self.assertEqual(AlternativVorname.objects.get().person, self.p3)

    def test_is_veranstalter(self):
        is_veranstalter1 = Person.is_veranstalter(self.p1)
        is_veranstalter2 = Person.is_veranstalter(self.p2)

        self.assertTrue(is_veranstalter1)
        self.assertFalse(is_veranstalter2)


class VeranstaltungTest(TransactionTestCase):
    def setUp(self):
        self.s = []
        self.s.append(Semester.objects.create(semester=20110, fragebogen='test', sichtbarkeit='ADM'))
        self.s.append(Semester.objects.create(semester=20115, fragebogen='test', sichtbarkeit='ADM'))

        self.default_params = {'semester': self.s[0], 'grundstudium': False, 'evaluieren': True}
        self.v = []
        self.v.append(Veranstaltung.objects.create(typ='v', name='Stoning I', **self.default_params))
        self.v.append(Veranstaltung.objects.create(typ='vu', name='Stoning II', **self.default_params))
        self.v.append(Veranstaltung.objects.create(typ='pr', name='Stoning III', **self.default_params))
        self.v.append(Veranstaltung.objects.create(typ='se', name='Stoning IV', **self.default_params))
        self.v.append(Veranstaltung.objects.create(typ='v',
                                                   name='Stoning V',
                                                   status=Veranstaltung.STATUS_GEDRUCKT,
                                                   **self.default_params))

    def test_get_evasys_typ(self):
        self.assertEqual(self.v[0].get_evasys_typ(), 1)
        self.assertEqual(self.v[1].get_evasys_typ(), 9)
        self.assertEqual(self.v[2].get_evasys_typ(), 5)
        self.assertEqual(self.v[3].get_evasys_typ(), 2)

    def test_status(self):
        self.assertEqual(self.v[0].status, Veranstaltung.STATUS_ANGELEGT)
        self.assertEqual(self.v[4].status, Veranstaltung.STATUS_GEDRUCKT)

    def test_log(self):
        is_admin = True
        is_scan = True

        self.v[0].log(is_admin, is_scan)
        self.assertEqual(Log.objects.count(), 0)

        self.v[0].log(is_admin, not is_scan)
        self.assertEqual(Log.objects.count(), 1)
        self.assertEqual(Log.objects.get(veranstaltung=self.v[0]).verursacher, 'Person')
        self.assertEqual(Log.objects.get(veranstaltung=self.v[0]).interface, 'Django Admin')

        self.v[1].log(not is_admin, is_scan)
        self.assertEqual(Log.objects.count(), 2)
        self.assertEqual(Log.objects.get(veranstaltung=self.v[1]).verursacher, 'Barcodescanner')
        self.assertEqual(Log.objects.get(veranstaltung=self.v[1]).interface, 'Barcodescanner')

        self.v[2].log(not is_admin, not is_scan)
        self.assertEqual(Log.objects.count(), 3)
        self.assertEqual(Log.objects.get(veranstaltung=self.v[2]).verursacher, 'Person')
        self.assertEqual(Log.objects.get(veranstaltung=self.v[2]).interface, 'Frontend')

    @staticmethod
    def change_status(v, new_status):
        v.status = new_status
        v.save()

    def test_get_next_state(self):
        v = self.v[0]
        self.assertEqual(v.get_next_state(), Veranstaltung.STATUS_GEDRUCKT)

        self.change_status(v, Veranstaltung.STATUS_GEDRUCKT)
        self.assertEqual(v.get_next_state(), Veranstaltung.STATUS_VERSANDT)

        self.change_status(v, Veranstaltung.STATUS_VERSANDT)
        self.assertEqual(v.get_next_state(), Veranstaltung.STATUS_BOEGEN_EINGEGANGEN)

        self.change_status(v, Veranstaltung.STATUS_BOEGEN_EINGEGANGEN)
        self.assertEqual(v.get_next_state(), Veranstaltung.STATUS_BOEGEN_GESCANNT)

        self.change_status(v, Veranstaltung.STATUS_BOEGEN_GESCANNT)
        self.assertIsNone(v.get_next_state())

    def test_has_uebung(self):
        self.assertTrue(self.v[1].has_uebung())
        self.assertFalse(self.v[0].has_uebung())

    def test_unicode(self):
        self.assertEqual(unicode(self.v[0]), 'Stoning I [v] (SS 2011)')

    def test_save(self):
        self.v[0].access_token = ''
        self.v[0].save()
        self.assertNotEqual(self.v[0].access_token, '')
        self.assertTrue(len(self.v[0].access_token) == 16)

    def test_unique(self):
        # Veranstaltung soll unique über name, lv_nr und semester sein
        with self.assertRaises(IntegrityError):
            Veranstaltung.objects.create(typ='v', name='Stoning I', **self.default_params)

        # eine Änderung einzelner Attribute soll trotzdem erlaubt sein
        try:
            # name
            Veranstaltung.objects.create(typ='v', name='Stoning XXIII', **self.default_params)
        except IntegrityError:
            self.fail()
        try:
            # lv_nr
            Veranstaltung.objects.create(typ='v', name='Stoning I', lv_nr='42', **self.default_params)
        except IntegrityError:
            self.fail()
        try:
            # semester
            params = self.default_params.copy()
            params['semester'] = self.s[1]
            Veranstaltung.objects.create(typ='v', name='Stoning I', **params)
        except IntegrityError:
            self.fail()

    def test_no_lang_set(self):
        """Wenn keine Sprache gesetzt ist gibt wird kein Bogen ausgewählt"""
        self.assertEqual(self.v[0].get_evasys_bogen(), '')

    def test_veranstalter_url(self):
        """Die URL für den Veranstalter soll die id und den Token enthalten"""
        url = self.v[0].link_veranstalter()
        url_parts = url.split('&')
        self.assertEqual(len(url_parts), 2)
        ver_id = self.v[0].id
        self.assertEqual(url_parts[0],
                         'https://www.fachschaft.informatik.tu-darmstadt.de/veranstalter/login/?vid=%d' % ver_id)
        access_token = self.v[0].access_token
        self.assertEquals('token=' + access_token, url_parts[1])


class EinstellungTest(TestCase):
    def setUp(self):
        self.a = Einstellung.objects.create(name='spam', wert='bacon')
        self.b = Einstellung.objects.create(name='sausage', wert='eggs')

    def test_get(self):
        self.assertEqual(Einstellung.get('spam'), self.a.wert)
        self.assertEqual(Einstellung.get('sausage'), self.b.wert)

    def test_unicode(self):
        self.assertEqual(unicode(self.a), 'spam = "bacon"')
        self.assertEqual(unicode(self.b), 'sausage = "eggs"')

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Einstellung.objects.create(name='spam', wert='cheese')


class MailvorlageTest(TestCase):
    def setUp(self):
        self.m = Mailvorlage.objects.create(subject='Nobody expects', body='the Spanish Inquisition')

    def test_unicode(self):
        self.assertEqual(unicode(self.m), u'Nobody expects')

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Mailvorlage.objects.create(subject='Nobody expects', body='the spammish repetition')


class ImportPersonTest(TestCase):
    def setUp(self):
        self.ip = ImportPerson.objects.create(vorname='Brian', nachname='Cohen')

    def test_full_name(self):
        self.assertEqual(self.ip.full_name(), 'Brian Cohen')

    def test_unicode(self):
        self.assertEqual(unicode(self.ip), 'Cohen, Brian')


class ImportCategoryTest(TestCase):
    def setUp(self):
        self.ic = ImportCategory.objects.create(name='Spam')

    def test_unicode(self):
        self.assertEqual(unicode(self.ic), 'Spam')


class ImportVeranstaltungTest(TestCase):
    def setUp(self):
        self.c = ImportCategory.objects.create(name='Sketches')
        self.iv = ImportVeranstaltung.objects.create(typ='v', name='Dead Parrot', lv_nr='42',
                                                     category=self.c, is_attended_course=True)

    def test_unicode(self):
        self.assertEqual(unicode(self.iv), 'Dead Parrot (42)')


class FragebogenTest(TestCase):
    def setUp(self):
        self.s, self.v = get_veranstaltung('v')
        self.f = Fragebogen2009.objects.create(veranstaltung=self.v, v_gesamt=1)

    def test_unicode(self):
        self.assertEqual(unicode(self.f), u'Fragebogen zu "Stoning I" (Vorlesung, SS 2011)')


class ErgebnisTest(TestCase):
    def setUp(self):
        self.s, self.vu = get_veranstaltung('vu')
        self.s, self.v = get_veranstaltung('v')
        self.eu = Ergebnis2009.objects.create(veranstaltung=self.vu, anzahl=5,
                                              v_gesamt=1, v_gesamt_count=2,
                                              ue_gesamt=2, ue_gesamt_count=3,
                                              v_feedbackpreis=3, v_feedbackpreis_count=4)
        self.e = Ergebnis2009.objects.create(veranstaltung=self.v, anzahl=5,
                                             v_gesamt=1, v_gesamt_count=2,
                                             ue_gesamt=2, ue_gesamt_count=3,
                                             v_feedbackpreis=3, v_feedbackpreis_count=4)
        self.parts_vl = [[None, 0], [1, 2]] + [[None, 0]] * 3
        self.parts_ue = [[2, 3]] + [[None, 0]] * 3
        self.parts_ue_empty = [[None, 0]] * 4
        self.parts_hidden = [[3, 4], [None, 0]]

    def test_values(self):
        self.assertListEqual(self.eu.values(), self.parts_vl + self.parts_ue)
        self.assertListEqual(self.e.values(), self.parts_vl + self.parts_ue_empty)

    def test_all_values(self):
        self.assertListEqual(self.eu.all_values(), self.parts_vl + self.parts_ue + self.parts_hidden)
        self.assertListEqual(self.e.all_values(), self.parts_vl + self.parts_ue_empty + self.parts_hidden)

    def test_unicode(self):
        self.assertEqual(unicode(self.e), u'Ergebnisse zu "Stoning I" (Vorlesung, Sommersemester 2011)')

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Ergebnis2009.objects.create(veranstaltung=self.v)


class KommentarTest(TestCase):
    def setUp(self):
        self.s, self.v = get_veranstaltung('v')
        self.p = []
        self.p.append(Person.objects.create(vorname='Brian', nachname='Cohen'))
        self.p.append(Person.objects.create(vorname='The', nachname='Crowd'))
        self.k = Kommentar.objects.create(veranstaltung=self.v, autor=self.p[0], text='You are all individuals!')

    def test_semester(self):
        self.assertEqual(self.k.semester(), self.s)

    def test_typ(self):
        self.assertEqual(self.k.typ(), 'Vorlesung')

    def test_name(self):
        self.assertEqual(self.k.name(), 'Stoning I')

    def test_unicode(self):
        self.assertEqual(unicode(self.k), u'Kommentar zu "Stoning I" (Vorlesung, Sommersemester 2011)')

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Kommentar.objects.create(veranstaltung=self.v, autor=self.p[1], text="I'm not.")


class LogTest(TestCase):

    @freeze_time("2016-12-06")
    def setUp(self):
        self.time = now()
        self.s, self.v = get_veranstaltung('v')
        self.log = Log.objects.create(veranstaltung=self.v, timestamp=self.time, status=Veranstaltung.STATUS_GEDRUCKT,
                                      verursacher='Person', interface='Django Admin')

    def test_name(self):
        self.assertEqual(self.log.veranstaltung.pk, self.v.pk)

    def test_timestamp(self):
        self.assertEqual(self.log.timestamp, self.time)

    def test_status(self):
        self.assertEqual(self.log.status, Veranstaltung.STATUS_GEDRUCKT)

    def test_verursacher(self):
        self.assertEqual(self.log.verursacher, 'Person')

    def test_interface(self):
        self.assertEqual(self.log.interface, 'Django Admin')
