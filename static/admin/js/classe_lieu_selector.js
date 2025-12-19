/**
 * JavaScript pour la sélection dynamique du lieu dans l'admin Classe
 * Charge les lieux disponibles en fonction de l'enseignant sélectionné
 */

(function() {
    'use strict';

    // Attendre que tout soit chargé (DOM + Select2)
    function waitForReady(callback) {
        if (document.readyState === 'complete') {
            setTimeout(callback, 800);
        } else {
            window.addEventListener('load', function() {
                setTimeout(callback, 800);
            });
        }
    }

    waitForReady(function() {
        initLieuSelector();
    });

    function initLieuSelector() {
        // Obtenir jQuery de Django
        var $ = django.jQuery || window.jQuery;
        if (!$) {
            console.error('Classe admin: jQuery non disponible');
            return;
        }

        console.log('Classe admin: Démarrage initialisation...');

        // Sélecteurs - essayer plusieurs variantes
        var enseignantField = $('#id_enseignant');
        var lieuSelectionField = $('#id_lieu_selection');

        // Vérifier que les champs existent
        if (!enseignantField.length) {
            console.log('Classe admin: Champ enseignant non trouvé');
            return;
        }

        if (!lieuSelectionField.length) {
            console.log('Classe admin: Champ lieu_selection non trouvé');
            return;
        }

        console.log('Classe admin: Champs trouvés - enseignant:', enseignantField.length, ', lieu:', lieuSelectionField.length);

        // URL de l'API AJAX
        var ajaxUrl = '/affectation/ajax/lieux-by-enseignant/';

        /**
         * Charge les lieux disponibles pour l'enseignant sélectionné
         */
        function loadLieux() {
            var enseignantId = getEnseignantId();
            console.log('Classe admin: loadLieux() appelé, enseignant ID:', enseignantId);

            if (!enseignantId || enseignantId === '') {
                resetLieuSelection();
                return;
            }

            // Afficher un indicateur de chargement
            lieuSelectionField.prop('disabled', true);
            lieuSelectionField.empty().append('<option value="">⏳ جاري التحميل... / Chargement...</option>');

            console.log('Classe admin: Envoi requête AJAX vers', ajaxUrl, 'avec enseignant_id=', enseignantId);

            $.ajax({
                url: ajaxUrl,
                method: 'GET',
                data: { enseignant_id: enseignantId },
                dataType: 'json',
                success: function(data) {
                    console.log('Classe admin: Réponse AJAX reçue:', data);
                    updateLieuOptions(data);
                },
                error: function(xhr, status, error) {
                    console.error('Classe admin: Erreur AJAX');
                    console.error('  Status:', status);
                    console.error('  Error:', error);
                    console.error('  Response:', xhr.responseText);
                    console.error('  Status Code:', xhr.status);
                    lieuSelectionField.empty().append('<option value="">❌ خطأ / Erreur: ' + error + '</option>');
                    lieuSelectionField.prop('disabled', false);
                }
            });
        }

        /**
         * Récupère l'ID de l'enseignant
         */
        function getEnseignantId() {
            var value = null;

            // Méthode 1: val() direct
            value = enseignantField.val();
            console.log('Classe admin: getEnseignantId via val():', value);

            if (value && value !== '') {
                return value;
            }

            // Méthode 2: Select2 data (si initialisé)
            try {
                if (enseignantField.data('select2')) {
                    var select2Data = enseignantField.select2('data');
                    console.log('Classe admin: Select2 data:', select2Data);
                    if (select2Data && select2Data.length > 0 && select2Data[0].id) {
                        return select2Data[0].id;
                    }
                }
            } catch(e) {
                console.log('Classe admin: Select2 non initialisé ou erreur:', e.message);
            }

            // Méthode 3: Chercher dans le DOM
            var selectedOption = enseignantField.find('option:selected');
            if (selectedOption.length && selectedOption.val()) {
                console.log('Classe admin: Valeur via option:selected:', selectedOption.val());
                return selectedOption.val();
            }

            return null;
        }

        /**
         * Met à jour les options du select lieu
         */
        function updateLieuOptions(data) {
            lieuSelectionField.empty();
            lieuSelectionField.append('<option value="">--- اختر المكان / Sélectionner le lieu ---</option>');

            // Ajouter info département
            if (data.departement_nom) {
                lieuSelectionField.append(
                    '<option value="" disabled style="font-weight: bold; background: #e3f2fd;">📍 ' +
                    escapeHtml(data.departement_nom) + '</option>'
                );
            }

            var hasOptions = false;

            // Amphithéâtres
            if (data.amphis && data.amphis.length > 0) {
                var amphiGroup = $('<optgroup label="🏛️ المدرجات / Amphithéâtres"></optgroup>');
                data.amphis.forEach(function(item) {
                    amphiGroup.append(
                        '<option value="amphi_dep_' + item.id + '">' +
                        escapeHtml(item.label) + ' [' + escapeHtml(item.semestres) + ']</option>'
                    );
                });
                lieuSelectionField.append(amphiGroup);
                hasOptions = true;
            }

            // Salles
            if (data.salles && data.salles.length > 0) {
                var salleGroup = $('<optgroup label="🚪 القاعات / Salles"></optgroup>');
                data.salles.forEach(function(item) {
                    salleGroup.append(
                        '<option value="salle_dep_' + item.id + '">' +
                        escapeHtml(item.label) + ' [' + escapeHtml(item.semestres) + ']</option>'
                    );
                });
                lieuSelectionField.append(salleGroup);
                hasOptions = true;
            }

            // Laboratoires
            if (data.laboratoires && data.laboratoires.length > 0) {
                var laboGroup = $('<optgroup label="🔬 المخابر / Laboratoires"></optgroup>');
                data.laboratoires.forEach(function(item) {
                    laboGroup.append(
                        '<option value="laboratoire_dep_' + item.id + '">' +
                        escapeHtml(item.label) + ' [' + escapeHtml(item.semestres) + ']</option>'
                    );
                });
                lieuSelectionField.append(laboGroup);
                hasOptions = true;
            }

            // Message si aucun lieu
            if (!hasOptions) {
                lieuSelectionField.append(
                    '<option value="" disabled style="color: #d32f2f;">⚠️ لا توجد أماكن / Aucun lieu disponible</option>'
                );
            }

            lieuSelectionField.prop('disabled', false);

            // Restaurer la valeur précédente si elle existe
            var currentValue = lieuSelectionField.data('current-value');
            if (currentValue) {
                lieuSelectionField.val(currentValue);
                lieuSelectionField.removeData('current-value');
            }

            console.log('Classe admin: Options mises à jour, hasOptions:', hasOptions);
        }

        /**
         * Réinitialise le select lieu
         */
        function resetLieuSelection() {
            lieuSelectionField.empty().append(
                '<option value="">--- اختر الأستاذ أولاً / Choisir d\'abord l\'enseignant ---</option>'
            );
            lieuSelectionField.prop('disabled', false);
            console.log('Classe admin: Sélection lieu réinitialisée');
        }

        /**
         * Échappe les caractères HTML
         */
        function escapeHtml(text) {
            if (!text) return '';
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // ══════════════════════════════════════════════════════════════
        // LIAISON DES ÉVÉNEMENTS
        // ══════════════════════════════════════════════════════════════

        // Sauvegarder la valeur actuelle
        var currentVal = lieuSelectionField.val();
        if (currentVal && currentVal !== '') {
            lieuSelectionField.data('current-value', currentVal);
            console.log('Classe admin: Valeur actuelle sauvegardée:', currentVal);
        }

        // 1. Événement change natif (fonctionne toujours)
        enseignantField.on('change.lieuSelector', function(e) {
            console.log('Classe admin: Événement CHANGE détecté');
            loadLieux();
        });

        // 2. Événements Select2 (pour Django admin autocomplete)
        enseignantField.on('select2:select.lieuSelector', function(e) {
            console.log('Classe admin: Événement SELECT2:SELECT détecté', e.params ? e.params.data : '');
            loadLieux();
        });

        enseignantField.on('select2:clear.lieuSelector', function(e) {
            console.log('Classe admin: Événement SELECT2:CLEAR détecté');
            resetLieuSelection();
        });

        enseignantField.on('select2:unselect.lieuSelector', function(e) {
            console.log('Classe admin: Événement SELECT2:UNSELECT détecté');
            resetLieuSelection();
        });

        // 3. Observer les changements DOM (backup)
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                    console.log('Classe admin: Mutation observée sur enseignant');
                    loadLieux();
                }
            });
        });

        // Observer l'élément select
        if (enseignantField[0]) {
            observer.observe(enseignantField[0], { attributes: true, attributeFilter: ['value'] });
        }

        // Charger les lieux si un enseignant est déjà sélectionné
        var initialId = getEnseignantId();
        if (initialId && initialId !== '') {
            console.log('Classe admin: Enseignant déjà sélectionné, chargement initial');
            loadLieux();
        } else {
            console.log('Classe admin: Aucun enseignant sélectionné initialement');
        }

        // Style du select
        lieuSelectionField.css({
            'min-height': '45px',
            'font-size': '14px',
            'width': '100%'
        });

        console.log('Classe admin: Initialisation terminée avec succès');
    }

})();