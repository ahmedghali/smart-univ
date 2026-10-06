# apps/noyau/commun/management/commands/populate_postes.py

from django.core.management.base import BaseCommand
from apps.noyau.commun.models import Poste


class Command(BaseCommand):
    help = 'Remplit la table des postes / يملأ جدول المناصب بالمناصب المحددة مسبقاً'

    def handle(self, *args, **kwargs):
        postes = [
            # ══════════════════════════════════════════════════════════
            # ENSEIGNANTS (niveau hiérarchique croissant)
            # ══════════════════════════════════════════════════════════
            
            {'code': 'enseignant', 'nom_ar': 'أستاذ', 'nom_fr': 'Enseignant', 
             'nom_ar_mini': 'أ', 'nom_fr_mini': 'Ens', 'type': 'enseignant', 'niveau': 1},
            
            {'code': 'chef_option', 'nom_ar': 'رئيس الخيارات', 'nom_fr': 'Chef Option', 
             'nom_ar_mini': 'ر.خ', 'nom_fr_mini': 'Ch.Opt', 'type': 'enseignant', 'niveau': 2},
            
            {'code': 'chef_specialite', 'nom_ar': 'رئيس التخصص', 'nom_fr': 'Chef de Spécialité', 
             'nom_ar_mini': 'ر.ت', 'nom_fr_mini': 'Ch.Spé', 'type': 'enseignant', 'niveau': 3},
            
            {'code': 'chef_filiere', 'nom_ar': 'رئيس الشعبة', 'nom_fr': 'Chef de Filière', 
             'nom_ar_mini': 'ر.ش', 'nom_fr_mini': 'Ch.Fil', 'type': 'enseignant', 'niveau': 3},
            
            {'code': 'president_csd', 'nom_ar': 'رئيس المجلس العلمي للقسم', 'nom_fr': 'Président CSD', 
             'nom_ar_mini': 'ر.م.ع.ق', 'nom_fr_mini': 'P.CSD', 'type': 'enseignant', 'niveau': 4},
            
            {'code': 'chef_dep_adj_p', 'nom_ar': 'نائب رئيس القسم للبيداغوجيا', 'nom_fr': 'Chef Dép. Adjoint Pédagogique', 
             'nom_ar_mini': 'ن.ر.ق.ب', 'nom_fr_mini': 'Ch.D.Adj.P', 'type': 'enseignant', 'niveau': 4},
            
            {'code': 'chef_dep_adj_pg', 'nom_ar': 'نائب رئيس القسم للدراسات العليا', 'nom_fr': 'Chef Dép. Adjoint PG', 
             'nom_ar_mini': 'ن.ر.ق.د', 'nom_fr_mini': 'Ch.D.Adj.PG', 'type': 'enseignant', 'niveau': 4},
            
            {'code': 'chef_departement', 'nom_ar': 'رئيس القسم', 'nom_fr': 'Chef de Département', 
             'nom_ar_mini': 'ر.ق', 'nom_fr_mini': 'Ch.Dép', 'type': 'enseignant', 'niveau': 5},
            
            {'code': 'president_csf', 'nom_ar': 'رئيس المجلس العلمي للكلية', 'nom_fr': 'Président CSF', 
             'nom_ar_mini': 'ر.م.ع.ك', 'nom_fr_mini': 'P.CSF', 'type': 'enseignant', 'niveau': 6},
            
            {'code': 'president_cd', 'nom_ar': 'رئيس المجلس التأديبي', 'nom_fr': 'Président CD', 
             'nom_ar_mini': 'ر.م.ت', 'nom_fr_mini': 'P.CD', 'type': 'enseignant', 'niveau': 6},
            
            {'code': 'vice_doyen_p', 'nom_ar': 'نائب العميد للبيداغوجيا', 'nom_fr': 'Vice-Doyen Pédagogique', 
             'nom_ar_mini': 'ن.ع.ب', 'nom_fr_mini': 'V.Doy.P', 'type': 'enseignant', 'niveau': 7},
            
            {'code': 'vice_doyen_pg', 'nom_ar': 'نائب العميد للدراسات العليا', 'nom_fr': 'Vice-Doyen PG', 
             'nom_ar_mini': 'ن.ع.د', 'nom_fr_mini': 'V.Doy.PG', 'type': 'enseignant', 'niveau': 7},
            
            {'code': 'doyen', 'nom_ar': 'العميد', 'nom_fr': 'Doyen', 
             'nom_ar_mini': 'ع', 'nom_fr_mini': 'Doy', 'type': 'enseignant', 'niveau': 8},
            
            {'code': 'vice_rect_p', 'nom_ar': 'نائب مدير الجامعة للبيداغوجيا', 'nom_fr': 'Vice-Recteur Pédagogique', 
             'nom_ar_mini': 'ن.م.ج.ب', 'nom_fr_mini': 'V.Rec.P', 'type': 'enseignant', 'niveau': 9},
            
            {'code': 'vice_rect_pg', 'nom_ar': 'نائب مدير الجامعة للدراسات العليا', 'nom_fr': 'Vice-Recteur PG', 
             'nom_ar_mini': 'ن.م.ج.د', 'nom_fr_mini': 'V.Rec.PG', 'type': 'enseignant', 'niveau': 9},
            
            {'code': 'recteur', 'nom_ar': 'مدير الجامعة', 'nom_fr': 'Recteur', 
             'nom_ar_mini': 'م.ج', 'nom_fr_mini': 'Rec', 'type': 'enseignant', 'niveau': 10},
            
            # ══════════════════════════════════════════════════════════
            # ÉTUDIANTS
            # ══════════════════════════════════════════════════════════
            
            {'code': 'etudiant', 'nom_ar': 'طالب', 'nom_fr': 'Étudiant', 
             'nom_ar_mini': 'ط', 'nom_fr_mini': 'Etu', 'type': 'etudiant', 'niveau': 0},
            
            {'code': 'delegue', 'nom_ar': 'مندوب الفوج', 'nom_fr': 'Délégué', 
             'nom_ar_mini': 'م.ف', 'nom_fr_mini': 'Dél', 'type': 'etudiant', 'niveau': 1},
            
            {'code': 'chef_club', 'nom_ar': 'رئيس نادي', 'nom_fr': 'Chef de Club', 
             'nom_ar_mini': 'ر.ن', 'nom_fr_mini': 'Ch.Cl', 'type': 'etudiant', 'niveau': 2},
            
            {'code': 'chef_association', 'nom_ar': 'رئيس جمعية', 'nom_fr': 'Chef Association', 
             'nom_ar_mini': 'ر.ج', 'nom_fr_mini': 'Ch.Ass', 'type': 'etudiant', 'niveau': 2},
            
            # ══════════════════════════════════════════════════════════
            # PERSONNEL ADMINISTRATIF
            # ══════════════════════════════════════════════════════════
            
            {'code': 'secretaire', 'nom_ar': 'أمين', 'nom_fr': 'Secrétaire', 
             'nom_ar_mini': 'أم', 'nom_fr_mini': 'Sec', 'type': 'admin', 'niveau': 2},
            
            {'code': 'scolarite', 'nom_ar': 'موظف مصلحة التعليم', 'nom_fr': 'Agent Scolarité', 
             'nom_ar_mini': 'م.ت', 'nom_fr_mini': 'Scol', 'type': 'admin', 'niveau': 2},
        ]

        created_count = 0
        updated_count = 0

        for poste_data in postes:
            poste, created = Poste.objects.update_or_create(
                code=poste_data['code'],
                defaults={
                    'nom_ar': poste_data['nom_ar'],
                    'nom_fr': poste_data['nom_fr'],
                    'nom_ar_mini': poste_data.get('nom_ar_mini', ''),
                    'nom_fr_mini': poste_data.get('nom_fr_mini', ''),
                    'type': poste_data['type'],
                    'niveau': poste_data.get('niveau', 0),
                }
            )
            
            if created:
                created_count += 1
                nom = poste_data.get('nom_fr', poste_data['nom_ar'])
                self.stdout.write(self.style.SUCCESS(f"✓ Cree / تم إنشاء: {nom}"))
            else:
                updated_count += 1
                nom = poste_data.get('nom_fr', poste_data['nom_ar'])
                self.stdout.write(self.style.WARNING(f"↻ MAJ / تم تحديث: {nom}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"═══════════════════════════════════════"))
        self.stdout.write(self.style.SUCCESS(f"  Terminé / تم الانتهاء من ملء جدول المناصب"))
        self.stdout.write(self.style.SUCCESS(f"  Nouveau: {created_count} | MAJ: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"═══════════════════════════════════════"))