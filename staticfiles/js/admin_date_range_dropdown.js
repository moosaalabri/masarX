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
                var name = $gte.attr('name'); 
                var prefix = name.substring(0, name.lastIndexOf('__gte'));
                var $lte = $('input[name="' + prefix + '__lte"]');

                if ($lte.length === 0) return; 

                var $container = $gte.closest('.admindatefilter');
                if ($container.length === 0) {
                    $container = $gte.closest('div[data-filter-name], li, .form-row, .card-body, .filter-wrapper');
                }
                if ($container.length === 0) $container = $gte.parent();

                if ($container.data('dropdown-init')) return;
                $container.data('dropdown-init', true);

                var $controls = $gte.closest('.controls');
                if ($controls.length === 0) {
                     $controls = $gte.parent();
                }
                
                // --- CHANGED: Use 'custom-select' and remove fixed width ---
                var $select = $('<select class="form-control custom-select admin-date-dropdown" style="width: auto; min-width: 120px; display: inline-block; margin-right: 5px;">' +
                    '<option value="any">Any Date</option>' +
                    '<option value="today">Today</option>' +
                    '<option value="7days">Last 7 Days</option>' +
                    '<option value="month">This Month</option>' +
                    '<option value="year">This Year</option>' +
                    '<option value="custom">Custom Range...</option>' +
                    '</select>');

                // --- CHANGED: Ensure controls are flex-friendly if we want "one row" ---
                // We'll wrap the inputs in a flex span if they aren't already
                $controls.css({
                    'display': 'inline-flex', 
                    'align-items': 'center', 
                    'gap': '5px'
                });
                
                // Style inputs to be small
                $gte.addClass('form-control form-control-sm').css('width', '110px');
                $lte.addClass('form-control form-control-sm').css('width', '110px');

                if ($controls.length) {
                    $controls.before($select);
                } else {
                    $gte.before($select);
                }

                var gteVal = $gte.val();
                var lteVal = $lte.val();

                if (gteVal || lteVal) {
                    $select.val('custom');
                    $controls.css('display', 'inline-flex'); // Show as flex
                } else {
                    $select.val('any');
                    $controls.hide();
                }

                $select.on('change', function() {
                    var val = $(this).val();
                    var today = new Date();

                    if (val === 'custom') {
                        $controls.css('display', 'inline-flex').hide().fadeIn(); // Animate in
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
        setTimeout(initDateRangeDropdown, 500);
    });
})(django.jQuery);
