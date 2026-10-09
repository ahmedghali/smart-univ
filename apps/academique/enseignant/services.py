from apps.academique.affectation.models import Ens_Dep
from apps.academique.departement.models import Departement
from apps.noyau.authentification.utils import get_user_postes_in_departement

TIME_SLOTS = [
    "08:00-09:30",
    "09:40-11:10",
    "11:20-12:50",
    "13:10-14:40",
    "14:50-16:20",
    "16:30-18:00",
    "18:00-19:30",
    "19:40-21:10",
]


WEEK_DAYS = ["Samedi", "Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi"]


def get_departement_from_session_or_enseignant(request, enseignant):
    """
    Récupère le département depuis la session ou depuis les affectations de l'enseignant.
    Garantit que my_Dep est toujours disponible pour le menu latéral.
    """
    # 1. Essayer depuis la session
    dep_id = request.session.get("selected_departement_id")
    if dep_id:
        try:
            return Departement.objects.get(id=dep_id)
        except Departement.DoesNotExist:
            pass

    # 2. Essayer depuis les affectations de l'enseignant
    try:
        ens_dep = Ens_Dep.objects.filter(enseignant=enseignant).first()
        if ens_dep:
            # Mettre à jour la session
            request.session["selected_departement_id"] = ens_dep.departement.id
            return ens_dep.departement
    except Exception:
        pass

    return None


def get_sidebar_context(request, enseignant, departement):
    """
    Retourne le contexte commun pour le menu latéral.
    À utiliser dans toutes les vues enseignant pour avoir un sidebar cohérent.
    """
    context = {
        "my_Ens": enseignant,
        "my_Dep": departement,
        "my_Fac": departement.faculte if departement else None,
        "departement": departement,
    }

    # Postes administratifs de l'enseignant dans ce département
    try:
        admin_postes = get_user_postes_in_departement(request.user, departement.id) if departement else []
        context["admin_postes"] = admin_postes
        context["has_admin_postes"] = admin_postes.exists() if hasattr(admin_postes, "exists") else bool(admin_postes)
    except Exception:
        context["admin_postes"] = []
        context["has_admin_postes"] = False

    # Autres départements de l'enseignant (hors département actuel)
    try:
        autres_departements = (
            Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
            .exclude(departement=departement)
            .select_related("departement", "departement__faculte")
            if departement
            else []
        )
        context["autres_departements"] = autres_departements
        context["has_autres_departements"] = (
            autres_departements.exists() if hasattr(autres_departements, "exists") else bool(autres_departements)
        )
    except Exception:
        context["autres_departements"] = []
        context["has_autres_departements"] = False

    return context


def get_real_department(enseignant):
    """Récupère le département principal (Permanent) ou premier actif de l'enseignant."""
    aff = (
        Ens_Dep.objects.filter(enseignant=enseignant, statut="Permanent", est_actif=True)
        .select_related("departement", "departement__faculte")
        .first()
    )
    if aff:
        return aff
    return (
        Ens_Dep.objects.filter(enseignant=enseignant, est_actif=True)
        .select_related("departement", "departement__faculte")
        .first()
    )


def count_classes_by_type(classes):
    """Compte les classes par type et retourne un dictionnaire."""
    counts = {"Cours": 0, "TP": 0, "TD": 0, "SS": 0}
    for c in classes:
        if c.type == "Cours":
            counts["Cours"] += 1
        elif c.type == "TP":
            counts["TP"] += 1
        elif c.type == "TD":
            counts["TD"] += 1
        elif c.type in ["Sortie Scientifique", "Sortie", "SS"]:
            counts["SS"] += 1
    counts["total"] = sum(counts.values())
    return counts


def _safe_str(value, default="-"):
    """Helper function to safely convert value to string, handling encoding errors."""
    if value is None:
        return default
    try:
        return str(value)
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            # Try to decode as latin-1 if utf-8 fails
            if isinstance(value, bytes):
                return value.decode("latin-1", errors="replace")
            return str(value).encode("latin-1", errors="replace").decode("utf-8", errors="replace")
        except Exception:
            return default


def fetch_and_update_scholar(enseignant):
    """
    Récupère et met à jour automatiquement les statistiques Google Scholar d'un enseignant :
    - scholar_publications_count
    - scholar_citations_count
    - scholar_h_index
    - scholar_i10_index
    - scholar_last_update
    Retourne un dict {'success': bool, 'message': str, ...}
    """
    import logging
    import re
    import requests
    from bs4 import BeautifulSoup
    from django.utils import timezone

    logger = logging.getLogger(__name__)

    if not enseignant.googlescholar:
        return {
            "success": False,
            "message": "لا يوجد رابط حساب Google Scholar مسجل لهذا الأستاذ. يرجى إضافته أولاً في الملف الشخصي.",
        }

    user_id = enseignant.scholar_user_id
    if not user_id:
        match = re.search(r"user=([a-zA-Z0-9_\-]+)", enseignant.googlescholar)
        if match:
            user_id = match.group(1)
        else:
            return {
                "success": False,
                "message": "رابط Google Scholar غير صالح. يجب أن يحتوي الرابط على معرف الباحث (user=...).",
            }

    url = f"https://scholar.google.com/citations?user={user_id}&hl=en&cstart=0&pagesize=100"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ar;q=0.7",
    }

    try:
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=12)

        # Fallback si Google renvoie 429 ou captcha
        if resp.status_code == 429 or "recaptcha" in resp.text.lower():
            try:
                from scholarly import scholarly

                author = scholarly.search_author_id(user_id)
                author_filled = scholarly.fill(author)
                publications = len(author_filled.get("publications", []))
                citations = author_filled.get("citedby", 0)
                h_index = author_filled.get("hindex", 0)
                i10_index = author_filled.get("i10index", 0)

                enseignant.scholar_publications_count = publications
                enseignant.scholar_citations_count = citations
                enseignant.scholar_h_index = h_index
                enseignant.scholar_i10_index = i10_index
                enseignant.scholar_last_update = timezone.now()
                enseignant.save(
                    update_fields=[
                        "scholar_publications_count",
                        "scholar_citations_count",
                        "scholar_h_index",
                        "scholar_i10_index",
                        "scholar_last_update",
                    ]
                )
                return {
                    "success": True,
                    "teacher_name": enseignant.get_nom_complet(),
                    "publications": publications,
                    "citations": citations,
                    "h_index": h_index,
                    "i10_index": i10_index,
                    "last_update": enseignant.scholar_last_update.strftime("%Y-%m-%d %H:%M"),
                    "message": "تم تحديث بيانات Google Scholar بنجاح.",
                }
            except Exception as sch_err:
                logger.warning(f"Scholarly fallback failed: {sch_err}")
                return {
                    "success": False,
                    "message": "تعذر الاتصال بـ Google Scholar حالياً بسبب كثرة الطلبات. يرجى المحاولة بعد قليل.",
                }

        if resp.status_code != 200:
            return {
                "success": False,
                "message": f"تعذر الاتصال بـ Google Scholar (رمز الاستجابة: {resp.status_code}).",
            }

        soup = BeautifulSoup(resp.text, "html.parser")

        # Vérifier si le profil existe
        table = soup.find("table", {"id": "gsc_rsb_st"})
        name_el = soup.find("div", {"id": "gsc_prf_in"})
        if not table and not name_el:
            return {
                "success": False,
                "message": "تعذر العثور على ملف الباحث في Google Scholar. يرجى التأكد من صحة الرابط.",
            }

        citations, h_index, i10_index = 0, 0, 0
        if table:
            tds = table.find_all("td", {"class": "gsc_rsb_std"})
            if len(tds) >= 1 and tds[0].text.strip().isdigit():
                citations = int(tds[0].text.strip())
            if len(tds) >= 3 and tds[2].text.strip().isdigit():
                h_index = int(tds[2].text.strip())
            if len(tds) >= 5 and tds[4].text.strip().isdigit():
                i10_index = int(tds[4].text.strip())

        # Publications de la 1ère page
        articles = soup.find_all("tr", {"class": "gsc_a_tr"})
        valid_articles = [a for a in articles if not a.find("td", {"class": "gsc_a_e"})]
        total_pubs = len(valid_articles)

        # Pagination si 100 articles sur la première page (chercheur prolifique)
        cstart = 100
        while len(valid_articles) == 100 and cstart < 1000:
            next_url = f"https://scholar.google.com/citations?user={user_id}&hl=en&cstart={cstart}&pagesize=100"
            try:
                next_resp = session.get(next_url, headers=headers, timeout=8)
                if next_resp.status_code == 200:
                    next_soup = BeautifulSoup(next_resp.text, "html.parser")
                    next_articles = next_soup.find_all("tr", {"class": "gsc_a_tr"})
                    valid_articles = [a for a in next_articles if not a.find("td", {"class": "gsc_a_e"})]
                    if not valid_articles:
                        break
                    total_pubs += len(valid_articles)
                    cstart += 100
                else:
                    break
            except Exception:
                break

        # Sauvegarder dans la base de données
        enseignant.scholar_publications_count = total_pubs
        enseignant.scholar_citations_count = citations
        enseignant.scholar_h_index = h_index
        enseignant.scholar_i10_index = i10_index
        enseignant.scholar_last_update = timezone.now()
        enseignant.save(
            update_fields=[
                "scholar_publications_count",
                "scholar_citations_count",
                "scholar_h_index",
                "scholar_i10_index",
                "scholar_last_update",
            ]
        )

        return {
            "success": True,
            "teacher_name": enseignant.get_nom_complet(),
            "publications": total_pubs,
            "citations": citations,
            "h_index": h_index,
            "i10_index": i10_index,
            "last_update": enseignant.scholar_last_update.strftime("%Y-%m-%d %H:%M"),
            "message": "تم تحديث بيانات Google Scholar بنجاح.",
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "انتهت مهلة الاتصال بخادم Google Scholar. يرجى المحاولة لاحقاً.",
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Google Scholar for {enseignant.id}: {e}")
        return {
            "success": False,
            "message": "حدث خطأ أثناء الاتصال بالخادم. يرجى التحقق من الاتصال بالإنترنت.",
        }
    except Exception as e:
        logger.exception(f"Unexpected error in scholar update for {enseignant.id}: {e}")
        return {
            "success": False,
            "message": f"حدث خطأ غير متوقع: {str(e)}",
        }

