// Dans votre fichier static/departement/js/list_etudiants.js

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
    
    // Charger les réformes
    $.ajax({
        type: 'GET',
        url: refsUrl,
        success: function(response) {
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
            console.error('Erreur lors du chargement des réformes:', error);
            refsSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
        }
    });

    // Charger les niveaux dynamiquement
    refsSelect.on('change', function() {
        const reformeId = $(this).val();
        nivsSelect.empty().append(new Option('-----إختر المستوى-----', ''));
        nivSpeDepSgSelect.empty().append(new Option('-----إختر الفوج-----', ''));
        $('#etudiants_list').empty();

        if (reformeId) {
            $.ajax({
                type: 'GET',
                url: nivsUrl.replace('0', reformeId),
                success: function(response) {
                    const niveaux = response.data;
                    niveaux.forEach(function(item) {
                        var newOption = new Option(item.niveau__nom_ar, item.niveau__id);
                        nivsSelect.append(newOption);
                    });
                },
                error: function(error) {
                    console.error('Erreur lors du chargement des niveaux:', error);
                    nivsSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
                }
            });
        }
    });

    // CORRECTION: Charger les NivSpeDep_SG (groupes) dynamiquement avec reforme_id
    nivsSelect.on('change', function() {
        const niveauId = $(this).val();
        const reformeId = refsSelect.val(); // AJOUT: Récupérer reforme_id
        nivSpeDepSgSelect.empty().append(new Option('-----إختر الفوج-----', ''));
        $('#etudiants_list').empty();

        console.log('🔍 DEPT DEBUG: niveauId =', niveauId, ', reformeId =', reformeId);

        if (niveauId && reformeId) { // CORRECTION: Vérifier aussi reforme_id
            $.ajax({
                type: 'GET',
                url: nivSpeDepSgUrl.replace('0', niveauId),
                data: { 'reforme_id': reformeId }, // AJOUT: Passer reforme_id en paramètre
                success: function(response) {
                    console.log('🔍 DEPT DEBUG groupes reçus:', response.data);
                    const nivSpeDepSgs = response.data;
                    nivSpeDepSgs.forEach(function(item) {
                        var newOption = new Option(item.full_name, item.id);
                        
                        // Si c'est un header de section, le désactiver
                        if (item.is_section_header) {
                            newOption.disabled = true;
                            newOption.style.fontWeight = 'bold';
                            newOption.style.backgroundColor = '#f0f0f0';
                        }
                        
                        nivSpeDepSgSelect.append(newOption);
                    });
                },
                error: function(error) {
                    console.error('Erreur lors du chargement des groupes:', error);
                    nivSpeDepSgSelect.html('<option disabled selected="True">Erreur lors du chargement.</option>');
                }
            });
        }
    });

    // Afficher la liste des étudiants selon NivSpeDep_SG avec DataTables
    $('#filter_form').on('submit', function(e) {
        e.preventDefault();
        var nivSpeDepSgId = $('#niv_spe_dep_sg').val();

        console.log("🔍 DEPT JS DEBUG: ID sélectionné:", nivSpeDepSgId);

        if (nivSpeDepSgId) {
            // Afficher un indicateur de chargement
            $('#etudiants_list').html('<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> جاري التحميل...</div>');
            
            $.ajax({
                type: 'POST',
                url: listUrl,
                data: {
                    'niv_spe_dep_sg': nivSpeDepSgId,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log("🔍 DEPT JS DEBUG: Réponse reçue:", response);
                    const etudiants = response.data;
                    
                    // Déterminer le titre selon la sélection
                    let titre_selection = "";
                    if (nivSpeDepSgId.startsWith('tous_')) {
                        titre_selection = " - جميع طلبة المستوى";
                    } else if (nivSpeDepSgId.startsWith('section_')) {
                        let section_name = nivSpeDepSgId.replace(/section_([^_]+).*/, '$1');
                        titre_selection = ` - قطاع ${section_name}`;
                    } else {
                        titre_selection = " - فوج محدد";
                    }
                    
                    let tableHtml = `
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-users"></i> 
                                    قائمة الطلبة${titre_selection} (${etudiants.length} طالب)
                                </h6>
                            </div>
                            <div class="card-body p-0">
                                <table id="etudiants_table" class="table table-striped mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th class="text-end">#</th>
                                            <th class="text-end">اللقب</th>
                                            <th class="text-end">الإسم</th>
                                            <th class="text-end">Nom</th>
                                            <th class="text-end">Prénom</th>
                                            <th class="text-end">رقم التسجيل</th>
                                            <th class="text-center">حالة المنصة</th>
                                            <th class="text-center">الإجراءات</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                    `;
                    let counter = 1;

                    if (etudiants.length > 0) {
                        etudiants.forEach(function(item) {
                            const statusBadge = item.inscrit_univ
                                ? '<span class="badge bg-success">مسجل</span>'
                                : '<span class="badge bg-warning">غير مسجل</span>';

                            const actionButtons = item.inscrit_univ
                                ? `<button class="btn btn-outline-danger btn-sm desinscrire-btn" data-id="${item.id}" title="إلغاء التسجيل"><i class="fas fa-user-times"></i></button>`
                                : `<button class="btn btn-outline-success btn-sm inscrire-btn" data-id="${item.id}" title="تسجيل في المنصة"><i class="fas fa-user-plus"></i></button>`;

                            const profileButton = `<button class="btn btn-outline-info btn-sm profile-btn" data-id="${item.id}" title="عرض الملف الشخصي"><i class="fas fa-eye"></i></button>`;

                            tableHtml += `
                                <tr>
                                    <td>${counter}</td>
                                    <td>${item.nom_ar || '-'}</td>
                                    <td>${item.prenom_ar || '-'}</td>
                                    <td>${item.nom_fr || '-'}</td>
                                    <td>${item.prenom_fr || '-'}</td>
                                    <td>${item.matricule || '-'}</td>
                                    <td class="text-center">${statusBadge}</td>
                                    <td class="text-center">${actionButtons} ${profileButton}</td>
                                </tr>
                            `;
                            counter++;
                        });
                    } else {
                        tableHtml += '<tr><td colspan="8" class="text-center text-muted">لا توجد طلبة في هذا الاختيار</td></tr>';
                    }
                    tableHtml += '</tbody></table></div></div>';

                    $('#etudiants_list').html(tableHtml);

                    // Initialiser DataTables si des étudiants existent
                    if (etudiants.length > 0) {
                        $('#etudiants_table').DataTable({
                            "paging": true,
                            "pageLength": 50,
                            "searching": true,
                            "ordering": true,
                            "info": true,
                            "columnDefs": [
                                { "orderable": false, "targets": [0, 6, 7] }
                            ],
                            "language": {
                                "url": "//cdn.datatables.net/plug-ins/1.13.4/i18n/ar.json"
                            },
                            "responsive": true
                        });
                    }
                },
                error: function(error) {
                    console.error('Erreur lors du chargement des étudiants:', error);
                    $('#etudiants_list').html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle"></i> 
                            خطأ في تحميل قائمة الطلبة
                        </div>
                    `);
                }
            });
        } else {
            $('#etudiants_list').html(`
                <div class="alert alert-warning">
                    <i class="fas fa-info-circle"></i> 
                    يرجى اختيار فوج لعرض قائمة الطلبة
                </div>
            `);
        }
    });

    // Gestion des boutons d'inscription/désinscription et profil
    $(document).on('click', '.inscrire-btn', function() {
        const etudiantId = $(this).data('id');
        const $button = $(this);
        const $row = $button.closest('tr');
        
        // Confirmation avant inscription
        if (!confirm('هل أنت متأكد من تسجيل هذا الطالب في المنصة؟')) {
            return;
        }
        
        // Désactiver le bouton pendant la requête
        $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
        
        $.ajax({
            type: 'POST',
            url: inscrireUrl,
            data: {
                'etudiant_id': etudiantId,
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Mettre à jour le badge de statut
                    $row.find('td:nth-child(7)').html('<span class="badge bg-success">مسجل</span>');
                    
                    // Remplacer le bouton d'inscription par celui de désinscription
                    $button.removeClass('btn-outline-success inscrire-btn')
                           .addClass('btn-outline-danger desinscrire-btn')
                           .attr('title', 'إلغاء التسجيل')
                           .html('<i class="fas fa-user-times"></i>')
                           .prop('disabled', false);
                    
                    // Afficher un message de succès
                    toastr.success('تم تسجيل الطالب بنجاح في المنصة');
                } else {
                    console.error('Erreur inscription:', response.error);
                    toastr.error('خطأ في تسجيل الطالب: ' + response.error);
                    $button.prop('disabled', false).html('<i class="fas fa-user-plus"></i>');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erreur AJAX inscription:', error);
                toastr.error('خطأ في الاتصال بالخادم');
                $button.prop('disabled', false).html('<i class="fas fa-user-plus"></i>');
            }
        });
    });

    $(document).on('click', '.desinscrire-btn', function() {
        const etudiantId = $(this).data('id');
        const $button = $(this);
        const $row = $button.closest('tr');
        
        // Confirmation avant désinscription
        if (!confirm('هل أنت متأكد من إلغاء تسجيل هذا الطالب من المنصة؟')) {
            return;
        }
        
        // Désactiver le bouton pendant la requête
        $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
        
        $.ajax({
            type: 'POST',
            url: desinscrireUrl,
            data: {
                'etudiant_id': etudiantId,
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Mettre à jour le badge de statut
                    $row.find('td:nth-child(7)').html('<span class="badge bg-warning">غير مسجل</span>');
                    
                    // Remplacer le bouton de désinscription par celui d'inscription
                    $button.removeClass('btn-outline-danger desinscrire-btn')
                           .addClass('btn-outline-success inscrire-btn')
                           .attr('title', 'تسجيل في المنصة')
                           .html('<i class="fas fa-user-plus"></i>')
                           .prop('disabled', false);
                    
                    // Afficher un message de succès
                    toastr.success('تم إلغاء تسجيل الطالب من المنصة بنجاح');
                } else {
                    console.error('Erreur désinscription:', response.error);
                    toastr.error('خطأ في إلغاء تسجيل الطالب: ' + response.error);
                    $button.prop('disabled', false).html('<i class="fas fa-user-times"></i>');
                }
            },
            error: function(xhr, status, error) {
                console.error('Erreur AJAX désinscription:', error);
                toastr.error('خطأ في الاتصال بالخادم');
                $button.prop('disabled', false).html('<i class="fas fa-user-times"></i>');
            }
        });
    });

    $(document).on('click', '.profile-btn', function() {
        const etudiantId = $(this).data('id');
        const profileUrl = `${profileUrlBase}${etudiantId}/profile/`;
        window.open(profileUrl, '_blank');
    });
});