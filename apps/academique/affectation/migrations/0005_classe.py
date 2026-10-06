# Generated manually for Classe model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affectation', '0004_add_infrastructure_affectations'),
        ('commun', '0004_alter_identification_options_and_more'),
        ('departement', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Classe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء / Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل / Date de modification')),
                ('observation', models.TextField(blank=True, default='', verbose_name='الملاحظة / Observation')),
                ('jour', models.CharField(choices=[('Samedi', 'السبت'), ('Dimanche', 'الأحد'), ('Lundi', 'الإثنين'), ('Mardi', 'الثلاثاء'), ('Mercredi', 'الأربعاء'), ('Jeudi', 'الخميس')], max_length=20, verbose_name='يوم الحصة / Jour')),
                ('temps', models.CharField(choices=[('08:00-09:30', 'الحصة الأولى 08:00-09:30'), ('09:40-11:10', 'الحصة الثانية 09:40-11:10'), ('11:20-12:50', 'الحصة الثالثة 11:20-12:50'), ('13:10-14:40', 'الحصة الرابعة 13:10-14:40'), ('14:50-16:20', 'الحصة الخامسة 14:50-16:20'), ('16:30-18:00', 'الحصة السادسة 16:30-18:00')], max_length=20, verbose_name='وقت الحصة / Créneau horaire')),
                ('type', models.CharField(choices=[('Cours', 'محاضرة / Cours'), ('TD', 'أعمال موجهة / TD'), ('TP', 'أعمال تطبيقية / TP'), ('Sortie', 'خرجة علمية / Sortie Scientifique')], max_length=20, verbose_name='نوع الحصة / Type de séance')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='معرف المكان / ID du lieu')),
                ('taux_avancement', models.PositiveSmallIntegerField(default=0, help_text='Pourcentage de progression (0-100)', verbose_name="نسبة التقدم / Taux d'avancement (%)")),
                ('seance_created', models.BooleanField(default=False, verbose_name='تم إنشاء الدروس / Séances créées')),
                ('abs_liste_Etu', models.BooleanField(default=False, verbose_name='تم إنشاء قائمة الغيابات / Liste absences créée')),
                ('notes_liste_Etu', models.BooleanField(default=False, verbose_name='تم إنشاء قائمة النقاط / Liste notes créée')),
                ('lien_moodle', models.URLField(blank=True, max_length=255, null=True, verbose_name='رابط Moodle / Lien Moodle')),
                ('content_type', models.ForeignKey(blank=True, limit_choices_to={'model__in': ['amphi_dep', 'salle_dep', 'laboratoire_dep']}, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='نوع المكان / Type de lieu')),
                ('enseignant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='affectation.ens_dep', verbose_name='الأستاذ / Enseignant')),
                ('matiere', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='departement.matiere', verbose_name='المادة / Matière')),
                ('niv_spe_dep_sg', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='departement.nivspedep_sg', verbose_name='الطلبة / Étudiants (Niveau-Spécialité-Section/Groupe)')),
                ('semestre', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classes', to='commun.semestre', verbose_name='السداسي / Semestre')),
            ],
            options={
                'verbose_name': 'حصة / Classe',
                'verbose_name_plural': 'حصص / Classes',
                'ordering': ['semestre', 'jour', 'temps', 'type'],
                'indexes': [
                    models.Index(fields=['semestre', 'jour', 'temps'], name='affectation_semestr_b1c2d3_idx'),
                    models.Index(fields=['enseignant', 'semestre'], name='affectation_enseign_a4e5f6_idx'),
                    models.Index(fields=['matiere', 'semestre'], name='affectation_matiere_d7e8f9_idx'),
                    models.Index(fields=['niv_spe_dep_sg', 'semestre'], name='affectation_niv_spe_g0h1i2_idx'),
                    models.Index(fields=['content_type', 'object_id'], name='affectation_content_j3k4l5_idx'),
                ],
                'unique_together': {('semestre', 'matiere', 'enseignant', 'niv_spe_dep_sg', 'jour', 'temps')},
            },
        ),
    ]