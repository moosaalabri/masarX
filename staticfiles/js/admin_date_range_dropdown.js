(function($) {
    // Masar Date Range Filter Layout Fix v4
    // Forces a horizontal layout for the Date Range Filter in Django Admin Sidebar
    // v4: Switches to type="date", removes Django's calendar shortcuts to prevent layout breakage.

    function initDateRangeDropdown() {
        
        // Find all "Greater Than or Equal" inputs (the start date of the range)
        var $gteInputs = $('input[name$="__gte"]');

        if ($gteInputs.length === 0) {
            return; // Not found yet
        }

        $gteInputs.each(function() {
            var $gte = $(this);
            if ($gte.data('masar-processed')) return;
            $gte.data('masar-processed', true);

            var name = $gte.attr('name'); 
            var prefix = name.substring(0, name.lastIndexOf('__gte'));
            var $lte = $('input[name="' + prefix + '__lte"]');

            if ($lte.length === 0) return; 

            // Locate the container
            var $parent = $gte.parent();

            // Create custom flex wrapper
            var $wrapper = $('<div class="masar-date-filter-row"></div>');
            
            // Create the Quick Select Dropdown
            var $select = $('<select class="form-control custom-select admin-date-dropdown">' +
                '<option value="any">Any</option>' +
                '<option value="today">Today</option>' +
                '<option value="7days">7 Days</option>' +
                '<option value="month">Month</option>' +
                '<option value="custom">Custom</option>' +
                '</select>');
            
            // CONVERT INPUTS TO HTML5 DATE
            // This gives us a native picker and removes the need for Django's clunky JS shortcuts
            $gte.attr('type', 'date').removeClass('vDateField');
            $lte.attr('type', 'date').removeClass('vDateField');

            // --- RESTRUCTURING DOM ---
            // 1. Insert wrapper before the start input
            $gte.before($wrapper);
            
            // 2. Move elements into wrapper
            $wrapper.append($select);
            $wrapper.append($gte);
            $wrapper.append($lte);

            // 3. AGGRESSIVE CLEANUP
            // Remove text nodes, BRs, AND Django's calendar shortcuts (.datetimeshortcuts)
            // We search the *original parent* for these leftovers.
            $parent.contents().filter(function() {
                return (
                    (this.nodeType === 3 && $.trim($(this).text()) !== '') || // Text
                    this.tagName === 'BR' || // Line breaks
                    $(this).hasClass('datetimeshortcuts') // Django Calendar Icons
                );
            }).remove();

            // Also hide any shortcuts that might be dynamically appended later (via CSS rule or observer)
            // But removing the 'vDateField' class above usually prevents Django from initializing them.

            // Logic for Dropdown Changes
            function formatDate(d) {
                var year = d.getFullYear();
                var month = ('0' + (d.getMonth() + 1)).slice(-2);
                var day = ('0' + d.getDate()).slice(-2);
                return year + '-' + month + '-' + day;
            }

            var gteVal = $gte.val();
            var lteVal = $lte.val();
            if (gteVal || lteVal) {
                $select.val('custom');
            } else {
                $select.val('any');
            }

            $select.on('change', function() {
                var val = $(this).val();
                var today = new Date();

                if (val === 'custom') {
                    // Do nothing, let user edit
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
                        }
                        $gte.val(startStr);
                        $lte.val(endStr);
                    }
                    // Trigger Form Submit
                    var $form = $gte.closest('form');
                    if ($form.length) {
                         $form.submit();
                    }
                }
            });
        });
    }

    $(document).ready(function() {
        initDateRangeDropdown();
        // Retry logic for stubborn renderers
        setTimeout(initDateRangeDropdown, 200);
        setTimeout(initDateRangeDropdown, 500);
        setTimeout(initDateRangeDropdown, 1000);
    });

})(django.jQuery);