# apps/noyau/personnel/management/commands/update_all_scholar.py

from django.core.management.base import BaseCommand
from apps.academique.enseignant.models import Enseignant
from django.utils import timezone
import time
import random
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Mettre à jour les statistiques Google Scholar avec support proxy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limiter le nombre de profils à mettre à jour',
        )
        
        parser.add_argument(
            '--department',
            type=int,
            default=None,
            help='ID du département spécifique',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la mise à jour même si récente',
        )
        
        parser.add_argument(
            '--use-proxy',
            action='store_true',
            help='Utiliser un proxy pour éviter le blocage Google',
        )
        
        parser.add_argument(
            '--delay',
            type=int,
            default=5,
            help='Délai minimum entre requêtes (en secondes, défaut: 5)',
        )
    
    def handle(self, *args, **options):
        limit = options.get('limit')
        department_id = options.get('department')
        force = options.get('force')
        use_proxy = options.get('use_proxy')
        delay = options.get('delay')
        
        # Import scholarly
        try:
            from scholarly import scholarly, ProxyGenerator
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Bibliothèque scholarly non installée.\n'
                    'Exécutez: pip install scholarly'
                )
            )
            return
        
        # Configurer le proxy si demandé
        if use_proxy:
            self.stdout.write("🔧 Configuration du proxy...")
            try:
                pg = ProxyGenerator()
                success = pg.FreeProxies()
                
                if success:
                    scholarly.use_proxy(pg)
                    self.stdout.write(self.style.SUCCESS("✅ Proxy configuré avec succès"))
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠️ Impossible de configurer le proxy\n"
                            "Continuation sans proxy (risque de blocage)"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Erreur proxy: {e}\n"
                        f"Continuation sans proxy..."
                    )
                )
        
        # Filtrer les enseignants
        enseignants = Enseignant.objects.exclude(
            googlescholar__isnull=True
        ).exclude(
            googlescholar=''
        )
        
        if department_id:
            enseignants = enseignants.filter(
                ens_dep__departement_id=department_id
            )
        
        # Filtrer selon force
        if not force:
            from django.db.models import Q
            from datetime import timedelta
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            enseignants = enseignants.filter(
                Q(scholar_last_update__isnull=True) | 
                Q(scholar_last_update__lt=seven_days_ago)
            )
        
        if limit:
            enseignants = enseignants[:limit]
        
        enseignants = enseignants.distinct()
        total = enseignants.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️ Aucun enseignant à mettre à jour'))
            return
        
        # Afficher le résumé
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS('🚀 MISE À JOUR GOOGLE SCHOLAR'))
        self.stdout.write("=" * 70)
        self.stdout.write(f"📊 Total à mettre à jour: {total}")
        if department_id:
            self.stdout.write(f"🏢 Département: {department_id}")
        if limit:
            self.stdout.write(f"🔢 Limite: {limit}")
        self.stdout.write(f"⚡ Mode: {'Force' if force else 'Normal'}")
        self.stdout.write(f"🔒 Proxy: {'Activé ✅' if use_proxy else 'Désactivé ⚠️'}")
        self.stdout.write(f"⏱️ Délai entre requêtes: {delay}s")
        self.stdout.write("=" * 70 + "\n")
        
        success = 0
        errors = 0
        blocked = 0
        
        for i, ens in enumerate(enseignants, 1):
            try:
                # Afficher la progression
                self.stdout.write(
                    f"[{i}/{total}] {ens.nom_ar} {ens.prenom_ar}...",
                    ending=''
                )
                
                # Extraire l'ID Scholar
                user_id = ens.scholar_user_id
                if not user_id:
                    self.stdout.write(self.style.WARNING(" ⚠️ URL invalide"))
                    errors += 1
                    continue
                
                # Délai aléatoire pour éviter rate limiting
                wait_time = random.uniform(delay, delay + 3)
                time.sleep(wait_time)
                
                # Tentative avec retry
                max_retries = 3
                retry_count = 0
                fetch_success = False
                
                while retry_count < max_retries and not fetch_success:
                    try:
                        author = scholarly.search_author_id(user_id)
                        author_filled = scholarly.fill(author)
                        fetch_success = True
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        
                        # Détection du type d'erreur
                        if "cannot fetch" in error_str or "429" in error_str:
                            retry_count += 1
                            
                            if retry_count < max_retries:
                                wait_time = 30 * retry_count
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"\n   ⚠️ Blocage détecté, attente {wait_time}s... "
                                        f"(Tentative {retry_count}/{max_retries})"
                                    )
                                )
                                time.sleep(wait_time)
                            else:
                                # Échec après toutes les tentatives
                                blocked += 1
                                self.stdout.write(
                                    self.style.ERROR(
                                        f" ❌ BLOQUÉ (après {max_retries} tentatives)"
                                    )
                                )
                                break
                        else:
                            # Autre type d'erreur
                            raise
                
                if not fetch_success:
                    errors += 1
                    continue
                
                # Extraire les statistiques
                publications = len(author_filled.get('publications', []))
                citations = author_filled.get('citedby', 0)
                h_index = author_filled.get('hindex', 0)
                i10_index = author_filled.get('i10index', 0)
                
                # Mettre à jour la base de données
                ens.scholar_publications_count = publications
                ens.scholar_citations_count = citations
                ens.scholar_h_index = h_index
                ens.scholar_i10_index = i10_index
                ens.scholar_last_update = timezone.now()
                
                ens.save(update_fields=[
                    'scholar_publications_count',
                    'scholar_citations_count',
                    'scholar_h_index',
                    'scholar_i10_index',
                    'scholar_last_update'
                ])
                
                success += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f" ✅ {publications} pubs | "
                        f"{citations} cits | "
                        f"H: {h_index}"
                    )
                )
                
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING(
                        "\n\n⚠️ Interruption par l'utilisateur"
                    )
                )
                break
                
            except Exception as e:
                errors += 1
                error_msg = str(e)[:50]
                self.stdout.write(self.style.ERROR(f" ❌ {error_msg}"))
                logger.error(f"Error updating {ens.nom_ar}: {str(e)}")
        
        # Afficher le résumé final
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS('✅ MISE À JOUR TERMINÉE'))
        self.stdout.write("=" * 70)
        self.stdout.write(f"✅ Succès:  {success}")
        self.stdout.write(f"❌ Erreurs: {errors}")
        
        if blocked > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"🚫 Bloqués: {blocked} (Google rate limiting)\n"
                    f"💡 Solutions:\n"
                    f"   - Réessayez avec: --use-proxy\n"
                    f"   - Attendez 1-2 heures\n"
                    f"   - Augmentez le délai: --delay 10"
                )
            )
        
        self.stdout.write(f"📊 Total:   {total}")
        
        if success > 0:
            success_rate = (success / total) * 100
            self.stdout.write(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        self.stdout.write("=" * 70)
        
        # Afficher quelques statistiques
        if success > 0:
            self.stdout.write("\n📊 STATISTIQUES GLOBALES:")
            from django.db.models import Avg, Max, Sum
            
            stats = Enseignant.objects.filter(
                scholar_publications_count__gt=0
            ).aggregate(
                avg_pubs=Avg('scholar_publications_count'),
                max_pubs=Max('scholar_publications_count'),
                total_pubs=Sum('scholar_publications_count'),
                avg_cits=Avg('scholar_citations_count'),
            )
            
            self.stdout.write(f"  Moyenne publications: {stats['avg_pubs']:.1f}")
            self.stdout.write(f"  Maximum publications: {stats['max_pubs']}")
            self.stdout.write(f"  Total publications:   {stats['total_pubs']}")
            self.stdout.write(f"  Moyenne citations:    {stats['avg_cits']:.0f}")
        
        self.stdout.write("")