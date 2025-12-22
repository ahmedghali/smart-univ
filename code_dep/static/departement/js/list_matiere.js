$(document).ready(function() {
    const refsSelect = $('#refs');
    const nivsSelect = $('#nivs');
    const sptsSelect = $('#spts');
    const semestresSelect = $('#semestres');
    const matieresTable = $('#matieres_table');
    const statusMessages = $('#status_messages');

    // Éléments pour l'import
    const btnShowImport = $('#btn_show_import');
    const btnImport = $('#btn_import');
    const btnCancelImport = $('#btn_cancel_import');
    const divImportSection = $('#div_import_section');
    const fileInput = $('#file_matieres');

    // Fonction pour obtenir les valeurs sélectionnées
    function getSelectedValues() {
        return {
            reforme: refsSelect.val(),
            niveau: nivsSelect.val(),
            specialite: sptsSelect.val(),
            semestre: semestresSelect.val()
        };
    }

    // Fonction pour réinitialiser les listes suivantes
    function resetFollowingSelects(fromIndex) {
        const selects = [refsSelect, nivsSelect, sptsSelect, semestresSelect];
        const defaultTexts = [
            '-----إختر الإصلاح-----',
            '-----إختر المستوى-----', 
            '-----إختر التخصص-----',
            '-----إختر السداسي-----'
        ];
        
        for (let i = fromIndex; i < selects.length; i++) {
            selects[i].empty().append(new Option(defaultTexts[i], ''));
        }
        matieresTable.empty();
        hideImportSection();
    }

    // 🔍 DEBUG: Vérifier que les variables sont définies
    console.log('=== DEBUG - VÉRIFICATION DES URLS ===');
    console.log('refsUrl:', typeof refsUrl !== 'undefined' ? refsUrl : 'NON DÉFINIE');
    console.log('nivsUrl:', typeof nivsUrl !== 'undefined' ? nivsUrl : 'NON DÉFINIE');
    console.log('sptsUrl:', typeof sptsUrl !== 'undefined' ? sptsUrl : 'NON DÉFINIE');
    console.log('semestresUrl:', typeof semestresUrl !== 'undefined' ? semestresUrl : 'NON DÉFINIE');
    console.log('matieresUrl:', typeof matieresUrl !== 'undefined' ? matieresUrl : 'NON DÉFINIE');
    console.log('importMatieresUrl:', typeof importMatieresUrl !== 'undefined' ? importMatieresUrl : 'NON DÉFINIE');
    console.log('=====================================');

    // Vérifier si les variables sont définies
    if (typeof refsUrl === 'undefined') {
        console.error('❌ refsUrl n\'est pas définie ! Vérifiez votre template HTML.');
        refsSelect.html('<option disabled selected="True">❌ URL non définie - Vérifiez le template</option>');
        return;
    }

    // Fonction pour afficher les messages de statut
    function showMessage(message, type = 'info') {
        const alertClass = type === 'error' ? 'alert-danger' : 
                          type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        const iconClass = type === 'error' ? 'fa-exclamation-triangle' : 
                         type === 'success' ? 'fa-check-circle' : 
                         type === 'warning' ? 'fa-exclamation-circle' : 'fa-info-circle';
        
        const messageHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="fas ${iconClass} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        statusMessages.html(messageHtml);
        
        setTimeout(() => {
            statusMessages.find('.alert').fadeOut();
        }, 8000);
    }

    // Fonction pour vérifier si toutes les sélections sont faites
    function areAllSelectionsValid() {
        return refsSelect.val() && nivsSelect.val() && sptsSelect.val() && semestresSelect.val();
    }

    // Fonction pour mettre à jour la visibilité des boutons d'import
    function updateImportButtonsVisibility() {
        if (areAllSelectionsValid()) {
            btnShowImport.show();
        } else {
            btnShowImport.hide();
            hideImportSection();
        }
    }

    // Fonction pour masquer la section d'import
    function hideImportSection() {
        divImportSection.hide();
        btnShowImport.show();
        fileInput.val('');
        statusMessages.empty();
    }

    // 1️⃣ Charger les réformes
    $.ajax({
        type: 'GET',
        url: refsUrl,
        success: function(response) {
            console.log('📥 Réponse réformes:', response);
            if (response.error) {
                console.log('Erreur:', response.error);
                refsSelect.html('<option disabled selected="True">Erreur: ' + response.error + '</option>');
            } else {
                const reformes = response.data;
                reformes.forEach(function(item) {
                    var newOption = new Option(item.nom_ar, item.id);
                    refsSelect.append(newOption);
                });
                console.log('✅ Réformes chargées:', reformes.length);
            }
        },
        error: function(error) {
            console.log('❌ Erreur réformes:', error);
            refsSelect.html('<option disabled selected="True">خطأ في التحميل</option>');
        }
    });

    // 2️⃣ Charger les niveaux dynamiquement
    refsSelect.on('change', function() {
        const selectedValues = getSelectedValues();
        console.log('🎯 Changement réforme:', selectedValues.reforme);
        resetFollowingSelects(1); // Réinitialiser niveaux, spécialités, semestres

        if (selectedValues.reforme) {
            $.ajax({
                type: 'GET',
                url: nivsUrl.replace('0', selectedValues.reforme),
                success: function(response) {
                    console.log('📥 Réponse niveaux:', response);
                    const niveaux = response.data;
                    niveaux.forEach(function(item) {
                        var newOption = new Option(item.niveau__nom_ar, item.niveau__id);
                        nivsSelect.append(newOption);
                    });
                    console.log('✅ Niveaux chargés:', niveaux.length);
                },
                error: function(error) {
                    console.log('❌ Erreur niveaux:', error);
                }
            });
        }
        updateImportButtonsVisibility();
    });

    // 3️⃣ Spécialités dépendent de RÉFORME + NIVEAU
    nivsSelect.on('change', function() {
        const selectedValues = getSelectedValues();
        console.log('🎯 Changement niveau:', selectedValues.niveau);
        resetFollowingSelects(2); // Réinitialiser spécialités, semestres

        if (selectedValues.reforme && selectedValues.niveau) {
            let url = sptsUrl.replace('0', selectedValues.niveau);
            
            $.ajax({
                type: 'POST',
                url: url,
                data: {
                    'reforme': selectedValues.reforme,
                    'niveau': selectedValues.niveau,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('📥 Réponse spécialités:', response);
                    const specialites = response.data;
                    specialites.forEach(function(item) {
                        // ✅ CORRECTION: Utiliser les bons champs
                        var newOption = new Option(item.specialite__nom_ar, item.specialite__id);
                        sptsSelect.append(newOption);
                    });
                    console.log('✅ Spécialités chargées:', specialites.length);
                },
                error: function(error) {
                    console.log('❌ Erreur lors du chargement des spécialités:', error);
                }
            });
        }
        updateImportButtonsVisibility();
    });

    // 4️⃣ Charger les semestres (dépendants ou indépendants)
    sptsSelect.on('change', function() {
        const selectedValues = getSelectedValues();
        console.log('🎯 Changement spécialité:', selectedValues.specialite);
        resetFollowingSelects(3); // Réinitialiser seulement semestres

        if (selectedValues.reforme && selectedValues.niveau && selectedValues.specialite) {
            $.ajax({
                type: 'POST',
                url: semestresUrl,
                data: {
                    'reforme': selectedValues.reforme,
                    'niveau': selectedValues.niveau,
                    'specialite': selectedValues.specialite,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('📥 Réponse semestres:', response);
                    const semestres = response.data;
                    semestres.forEach(function(item) {
                        var newOption = new Option(item.nom_ar, item.id);
                        semestresSelect.append(newOption);
                    });
                    console.log('✅ Semestres chargés:', semestres.length);
                },
                error: function(error) {
                    console.log('❌ Erreur lors du chargement des semestres:', error);
                }
            });
        }
        updateImportButtonsVisibility();
    });

    semestresSelect.on('change', function() {
        matieresTable.empty();
        hideImportSection();
        updateImportButtonsVisibility();
        console.log('🎯 Changement semestre:', semestresSelect.val());
    });

    // 5️⃣ Affichage des matières
    $('#btn_afficher').on('click', function() {
        const selectedValues = getSelectedValues();
        console.log('🎯 Clic afficher matières:', selectedValues);

        if (selectedValues.reforme && selectedValues.niveau && selectedValues.specialite && selectedValues.semestre) {
            statusMessages.empty();
            
            $.ajax({
                type: 'POST',
                url: matieresUrl,
                data: {
                    'reforme': selectedValues.reforme,
                    'niveau': selectedValues.niveau,
                    'specialite': selectedValues.specialite,
                    'semestre': selectedValues.semestre,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('📥 Réponse matières:', response);
                    const matieres = response.data;
                    
                    if (matieres.length === 0) {
                        matieresTable.html('<div class="alert alert-info"><i class="fas fa-info-circle"></i> لا توجد مواد مسجلة لهذا التحديد</div>');
                        return;
                    }
                    
                    let tableHtml = `
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="fas fa-list"></i> قائمة المواد (${matieres.length} مادة)</h6>
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover mb-0">
                                        <thead class="table-dark">
                                            <tr>
                                                <th>#</th>
                                                <th>المادة</th>
                                                <th>Matière</th>
                                                <th>Code-Unité</th>
                                                <th>Code</th>
                                                <th>Coeff</th>
                                                <th>Crédit</th>
                                                <th>Unité</th>
                                                <th>الوحدة</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                    `;
                    
                    let counter = 1;
                    matieres.forEach(function(item) {
                        tableHtml += `
                            <tr>
                                <td class="fw-bold">${counter}</td>
                                <td>${item.nom_ar || '-'}</td>
                                <td>${item.nom_fr || '-'}</td>
                                <td>${item.unite__code || '-'}</td>
                                <td><span class="badge bg-primary">${item.code}</span></td>
                                <td>${item.coeff}</td>
                                <td>${item.credit}</td>
                                <td>${item.unite__nom_fr || '-'}</td>
                                <td>${item.unite__nom_ar || '-'}</td>
                            </tr>
                        `;
                        counter++;
                    });
                    
                    tableHtml += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;
                    matieresTable.html(tableHtml);
                    console.log('✅ Tableau des matières affiché');
                },
                error: function(error) {
                    console.log('❌ Erreur matières:', error);
                    matieresTable.html('<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> خطأ في تحميل المواد</div>');
                }
            });
        } else {
            showMessage('يجب اختيار جميع الحقول لعرض المواد', 'warning');
        }
    });

    // ==================== SECTION IMPORT ====================
    
    // Gestion des boutons d'import
    btnShowImport.on('click', function() {
        console.log('🎯 Clic sur btnShowImport');
        if (areAllSelectionsValid()) {
            divImportSection.show();
            btnShowImport.hide();
            statusMessages.empty();
            console.log('✅ Section d\'import affichée');
        } else {
            showMessage('يجب اختيار جميع الحقول قبل إضافة المواد', 'error');
            console.log('❌ Toutes les sélections ne sont pas valides');
        }
    });

    btnCancelImport.on('click', function() {
        console.log('🎯 Clic sur btnCancelImport');
        hideImportSection();
    });

    // Validation du fichier lors de la sélection
    fileInput.on('change', function() {
        const file = this.files[0];
        console.log('📁 Fichier sélectionné:', file);
        
        if (file) {
            const fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
                showMessage('يجب أن يكون الملف من نوع Excel (.xlsx أو .xls)', 'error');
                $(this).val('');
                return;
            }
            
            const fileSize = (file.size / 1024 / 1024).toFixed(2);
            showMessage(`تم اختيار الملف: ${file.name} (${fileSize} MB)`, 'info');
        }
    });

    // Import des matières
    btnImport.on('click', function() {
        console.log('🎯 Clic sur btnImport');
        
        const selectedValues = getSelectedValues();
        const file = fileInput[0].files[0];

        console.log('📋 Données pour import:', {
            selectedValues, 
            file: file ? file.name : 'Aucun'
        });

        if (!areAllSelectionsValid()) {
            showMessage('يجب اختيار جميع الحقول', 'error');
            return;
        }

        if (!file) {
            showMessage('يجب اختيار ملف Excel', 'error');
            return;
        }

        // Vérifier que importMatieresUrl est définie
        if (typeof importMatieresUrl === 'undefined') {
            showMessage('خطأ: رابط الاستيراد غير محدد', 'error');
            console.error('❌ importMatieresUrl non définie !');
            return;
        }

        console.log('📡 URL d\'import:', importMatieresUrl);

        // Préparer les données pour l'envoi
        const formData = new FormData();
        formData.append('file_matieres', file);
        formData.append('reforme', selectedValues.reforme);
        formData.append('niveau', selectedValues.niveau);
        formData.append('specialite', selectedValues.specialite);
        formData.append('semestre', selectedValues.semestre);
        formData.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());

        // Désactiver le bouton pendant l'upload
        const originalText = btnImport.html();
        btnImport.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> جاري الاستيراد...');

        $.ajax({
            type: 'POST',
            url: importMatieresUrl,
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function() {
                console.log('📤 Début de l\'upload...');
            },
            success: function(response) {
                console.log('✅ Réponse d\'import:', response);
                
                if (response.success) {
                    let message = `تم الاستيراد بنجاح!<br>`;
                    if (response.created > 0) {
                        message += `<strong>جديد:</strong> ${response.created} مادة<br>`;
                    }
                    if (response.updated > 0) {
                        message += `<strong>محدث:</strong> ${response.updated} مادة<br>`;
                    }
                    if (response.errors > 0) {
                        message += `<strong>أخطاء:</strong> ${response.errors} سطر`;
                    }
                    
                    showMessage(message, 'success');
                    hideImportSection();
                    
                    // Actualiser la liste des matières automatiquement
                    setTimeout(() => {
                        $('#btn_afficher').click();
                    }, 1000);
                } else {
                    showMessage(response.message || 'حدث خطأ أثناء الاستيراد', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error('❌ Erreur AJAX d\'import:', error);
                console.error('Status:', status);
                console.error('Response:', xhr.responseText);
                
                let errorMessage = 'حدث خطأ في الاتصال مع الخادم';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.status === 404) {
                    errorMessage = 'خطأ 404: رابط الاستيراد غير موجود';
                } else if (xhr.status === 500) {
                    errorMessage = 'خطأ 500: خطأ في الخادم';
                }
                
                showMessage(errorMessage, 'error');
            },
            complete: function() {
                console.log('🏁 Import terminé');
                // Réactiver le bouton
                btnImport.prop('disabled', false).html(originalText);
            }
        });
    });

    // ==================== FIN SECTION IMPORT ====================
});