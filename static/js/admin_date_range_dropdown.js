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
            // Find start date inputs for 'created_at' (or generic generic approach for any range filter)
            // rangefilter inputs typically have names ending in __gte and __lte
            var $gteInputs = $('input[name$="__gte"]');

            $gteInputs.each(function() {
                var $gte = $(this);
                var name = $gte.attr('name'); 
                var prefix = name.substring(0, name.lastIndexOf('__gte'));
                var $lte = $('input[name="' + prefix + '__lte"]');

                if ($lte.length === 0) return; // Not a pair

                // Find a container to inject the dropdown. 
                // In Jazzmin/Standard, this might be inside a .admindatefilter div, 
                // or just a li, or a div.controls.
                // We'll look for the closest container that seems to wrap the filter.
                
                // Try to find .admindatefilter first
                var $container = $gte.closest('.admindatefilter');
                if ($container.length === 0) {
                    // Fallback for Jazzmin or other themes: closest .card-body or similar?
                    // Or just the parent form/div
                    $container = $gte.closest('div[data-filter-name], li, .form-row, .card-body');
                }
                
                if ($container.length === 0) $container = $gte.parent();

                if ($container.data('dropdown-init')) return;
                $container.data('dropdown-init', true);

                // Hide the original inputs/controls container
                // We need to be careful not to hide the form itself if it's the main filter form
                // Usually rangefilter puts inputs in a 'controls' div or paragraphs.
                var $controls = $gte.closest('.controls');
                if ($controls.length === 0) {
                     // Try to find the immediate parent if it contains both inputs
                     $controls = $gte.parent();
                }
                
                // Create Select
                var $select = $('<select class="form-control admin-date-dropdown" style="width: 100%; margin-bottom: 10px; margin-top: 5px;">' +
                    '<option value="any">Any Date</option>' +
                    '<option value="today">Today</option>' +
                    '<option value="7days">Last 7 Days</option>' +
                    '<option value="month">This Month</option>' +
                    '<option value="year">This Year</option>' +
                    '<option value="custom">Custom Range...</option>' +
                    '</select>');

                // Inject before the controls (inputs)
                if ($controls.length) {
                    $controls.before($select);
                } else {
                    $gte.before($select);
                }

                // Initial State
                var gteVal = $gte.val();
                var lteVal = $lte.val();

                if (gteVal || lteVal) {
                    $select.val('custom');
                    $controls.show();
                } else {
                    $select.val('any');
                    $controls.hide();
                }

                $select.on('change', function() {
                    var val = $(this).val();
                    var today = new Date();

                    if (val === 'custom') {
                        $controls.slideDown();
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
                        
                        // Submit form
                        // In Jazzmin, the filter form might be #changelist-search or similiar
                        var $form = $gte.closest('form');
                        if ($form.length) {
                            $form.submit();
                        } else {
                             // Try to find a global apply button or trigger change?
                             // Some admin themes auto-submit on change.
                             // rangefilter usually has a submit button.
                             var $btn = $container.find('input[type="submit"], button[type="submit"]');
                             if ($btn.length) $btn.click();
                        }
                    }
                });
            });
        }

        // Run init
        initDateRangeDropdown();
        
        // Safety: Run again after a slight delay in case of dynamic loading (unlikely in admin but possible)
        setTimeout(initDateRangeDropdown, 500);
    });
})(django.jQuery);