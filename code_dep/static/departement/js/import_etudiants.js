$(document).ready(function() {
    // Setup CSRF token for AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
            }
        }
    });

    const refsSelect = $('#refs');
    const nivsSelect = $('#nivs');
    const nivSpeDepSgSelect = $('#niv_spe_dep_sg');
    const importResult = $('#import_result');

    // Charger les réformes avec la fonction corrigée
    $.ajax({
        type: 'GET',
        url: refsUrl,
        success: function(response) {
            console.log('🔍 Réformes reçues:', response.data);
            if (response.error) {
                refsSelect.html('<option disabled selected="True">Erreur: ' + response.error + '</option>');
            } else {
                const reformes = response.data;
                reformes.forEach(function(item) {
                    var newOption = new Option(item.nom_ar, item.id);
                    refsSelect.append(newOption);
                });
            }
        },
        error: function(error) {
            console.error('Erreur réformes:', error);
            refsSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
        }
    });

    // Charger les niveaux dynamiquement avec la fonction corrigée
    refsSelect.on('change', function() {
        const reformeId = $(this).val();
        nivsSelect.empty().append(new Option('-----إختر المستوى-----', ''));
        nivSpeDepSgSelect.empty().append(new Option('-----إختر الفوج-----', ''));
        importResult.empty();

        console.log('🔍 Reforme sélectionnée:', reformeId);

        if (reformeId) {
            $.ajax({
                type: 'GET',
                url: nivsUrl.replace('0', reformeId),
                success: function(response) {
                    console.log('🔍 Niveaux reçus:', response.data);
                    const niveaux = response.data;
                    niveaux.forEach(function(item) {
                        var newOption = new Option(item.niveau__nom_ar, item.niveau__id);
                        nivsSelect.append(newOption);
                    });
                },
                error: function(error) {
                    console.error('Erreur niveaux:', error);
                    nivsSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
                }
            });
        }
    });

    // Charger les NivSpeDep_SG (groupes) dynamiquement avec reforme_id
    nivsSelect.on('change', function() {
        const niveauId = $(this).val();
        const reformeId = refsSelect.val();
        nivSpeDepSgSelect.empty().append(new Option('-----إختر الفوج-----', ''));
        importResult.empty();

        console.log('🔍 Niveau sélectionné:', niveauId, ', Reforme:', reformeId);

        if (niveauId && reformeId) {
            $.ajax({
                type: 'GET',
                url: nivSpeDepSgUrl.replace('0', niveauId),
                data: { 'reforme_id': reformeId }, // Passer reforme_id pour filtrer
                success: function(response) {
                    console.log('🔍 Groupes reçus:', response.data);
                    const nivSpeDepSgs = response.data;
                    if (nivSpeDepSgs.length === 0) {
                        nivSpeDepSgSelect.html('<option disabled selected="True">لا توجد مجموعات متاحة</option>');
                    } else {
                        nivSpeDepSgs.forEach(function(item) {
                            var newOption = new Option(item.full_name, item.id);
                            nivSpeDepSgSelect.append(newOption);
                        });
                    }
                },
                error: function(error) {
                    console.error('Erreur groupes:', error);
                    nivSpeDepSgSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
                }
            });
        }
    });

    // Validation du formulaire avant soumission
    $('form[name="import_form"]').on('submit', function(e) {
        const reforme = $('#refs').val();
        const niveau = $('#nivs').val();
        const groupe = $('#niv_spe_dep_sg').val();
        const fichier = $('#excel_file').val();

        if (!reforme || !niveau || !groupe || !fichier) {
            e.preventDefault();
            alert('يرجى ملء جميع الحقول واختيار ملف Excel');
            return false;
        }

        // Confirmer l'importation
        if (!confirm('هل أنت متأكد من استيراد الطلاب؟ سيتم إنشاء حسابات جديدة للطلاب.')) {
            e.preventDefault();
            return false;
        }

        // Afficher indicateur de chargement
        $(this).find('button[type="submit"]').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> جاري الاستيراد...');
    });
});