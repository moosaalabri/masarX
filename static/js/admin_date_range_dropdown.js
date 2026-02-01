(function($) {
    // Masar Date Range Filter Layout Fix v3
    // Forces a horizontal layout for the Date Range Filter in Django Admin Sidebar

    function initDateRangeDropdown() {
        console.log("Masar Date Filter: Initializing v3...");
        
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

            // Locate the container in the sidebar.
            // Usually it's inside a <li class="... field-created_at ..."> or similar.
            // We want to find the direct parent that holds these inputs.
            var $parent = $gte.parent();

            // Create our custom flex wrapper
            var $wrapper = $('<div class="masar-date-filter-row"></div>');
            $wrapper.css({
                'display': 'flex',
                'flex-direction': 'row',
                'align-items': 'center',
                'gap': '3px',
                'width': '100%',
                'margin-bottom': '10px'
            });

            // Create the Quick Select Dropdown
            var $select = $('<select class="form-control custom-select admin-date-dropdown">' +
                '<option value="any">Any</option>' +
                '<option value="today">Today</option>' +
                '<option value="7days">7 Days</option>' +
                '<option value="month">Month</option>' +
                '<option value="custom">Custom</option>' +
                '</select>');
            
            $select.css({
                'width': '34%', 
                'min-width': '60px',
                'height': '30px',
                'padding': '0 4px',
                'font-size': '11px'
            });

            // Style inputs
            var inputStyle = {
                'width': '33%',
                'min-width': '0',
                'height': '30px',
                'padding': '4px',
                'font-size': '11px'
            };
            $gte.css(inputStyle).attr('placeholder', 'Start');
            $lte.css(inputStyle).attr('placeholder', 'End');

            // --- RESTRUCTURING DOM ---
            // 1. Insert wrapper before the start input
            $gte.before($wrapper);
            
            // 2. Move elements into wrapper
            $wrapper.append($select);
            $wrapper.append($gte);
            $wrapper.append($lte);

            // 3. Cleanup: Hide any left-over text nodes (like "-", "From", "To") or <br> in the parent
            $parent.contents().filter(function() {
                return (this.nodeType === 3 && $.trim($(this).text()) !== '') || this.tagName === 'BR';
            }).remove();

            // Logic for Dropdown Changes
            // Helper to format date as YYYY-MM-DD
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
                    // Trigger Form Submit (Changes URL)
                    // Try to find the filter form
                    var $form = $gte.closest('form'); // Usually #changelist-search
                    if ($form.length) {
                         $form.submit();
                    } else {
                        // Sometimes filters are links, but date range usually has a button or relies on form
                        // If there is an "Apply" button nearby?
                        var $applyBtn = $parent.closest('.admindatefilter').find('input[type="submit"], button');
                        if ($applyBtn.length) {
                            $applyBtn.click();
                        } else {
                            // Fallback: reload page with query params (complex, skip for now, rely on standard form)
                        }
                    }
                }
            });
        });
    }

    $(document).ready(function() {
        // Run immediately
        initDateRangeDropdown();
        
        // And retry a few times to catch slow rendering
        setTimeout(initDateRangeDropdown, 200);
        setTimeout(initDateRangeDropdown, 500);
        setTimeout(initDateRangeDropdown, 1000);
    });

})(django.jQuery);
