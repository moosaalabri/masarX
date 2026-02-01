(function($) {
    $(document).ready(function() {
        // Helper to format date as YYYY-MM-DD
        function formatDate(d) {
            var year = d.getFullYear();
            var month = ('0' + (d.getMonth() + 1)).slice(-2);
            var day = ('0' + d.getDate()).slice(-2);
            return year + '-' + month + '-' + day;
        }

        function initDateRangeDropdown() {
            var $gteInputs = $('input[name$="__gte"]');

            $gteInputs.each(function() {
                var $gte = $(this);
                // Prevent double init
                if ($gte.data('dropdown-processed')) return;
                $gte.data('dropdown-processed', true);

                var name = $gte.attr('name'); 
                var prefix = name.substring(0, name.lastIndexOf('__gte'));
                var $lte = $('input[name="' + prefix + '__lte"]');

                if ($lte.length === 0) return; 

                var $container = $gte.closest('.admindatefilter');
                if ($container.length === 0) {
                    $container = $gte.closest('div[data-filter-name], li, .form-row, .card-body, .filter-wrapper');
                }
                if ($container.length === 0) $container = $gte.parent();

                // Find the direct wrapper of the inputs (usually .controls)
                var $controls = $gte.closest('.controls');
                if ($controls.length === 0) {
                     $controls = $gte.parent();
                }
                $controls.addClass('date-filter-controls'); // Hook for CSS
                
                // --- Dropdown ---
                var $select = $('<select class="form-control custom-select admin-date-dropdown">' +
                    '<option value="any">Any</option>' + // Shortened text
                    '<option value="today">Today</option>' +
                    '<option value="7days">7 Days</option>' +
                    '<option value="month">Month</option>' +
                    '<option value="custom">Custom</option>' +
                    '</select>');

                // --- Inputs Styling ---
                $gte.addClass('form-control form-control-sm date-input');
                $lte.addClass('form-control form-control-sm date-input');
                $gte.attr('placeholder', 'Start'); // Short placeholder
                $lte.attr('placeholder', 'End');

                // Insert Dropdown INSIDE the flex container (at start)
                if ($controls.length) {
                    $controls.prepend($select);
                } else {
                    $gte.before($select);
                }

                // Initial State
                var gteVal = $gte.val();
                var lteVal = $lte.val();

                if (gteVal || lteVal) {
                    $select.val('custom');
                } else {
                    $select.val('any');
                }

                // Event Listener
                $select.on('change', function() {
                    var val = $(this).val();
                    var today = new Date();

                    if (val === 'custom') {
                        // Inputs are always visible in our new layout, just ensure they are enabled/cleared if needed
                    } else {
                        if (val === 'any') {
                            $gte.val('');
                            $lte.val('');
                        } else {
                            var startStr = '';
                            var endStr = formatDate(today);

                            if (val === 'today') {
                                startStr = formatDate(today);
                            } else if (val === '7days') {
                                var past = new Date();
                                past.setDate(today.getDate() - 7);
                                startStr = formatDate(past);
                            } else if (val === 'month') {
                                var firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                                startStr = formatDate(firstDay);
                            } else if (val === 'year') {
                                var firstDay = new Date(today.getFullYear(), 0, 1);
                                startStr = formatDate(firstDay);
                            }

                            $gte.val(startStr);
                            $lte.val(endStr);
                        }
                        
                        // Auto-submit
                        var $form = $gte.closest('form');
                        if ($form.length) {
                            $form.submit();
                        } else {
                             var $btn = $container.find('input[type="submit"], button[type="submit"]');
                             if ($btn.length) $btn.click();
                        }
                    }
                });
            });
        }

        initDateRangeDropdown();
        // Re-run safely for dynamic content
        setTimeout(initDateRangeDropdown, 500);
    });
})(django.jQuery);