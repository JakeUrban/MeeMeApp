/**
 * Bind together javascript libraries used in this application.
 * Compile these with 'browserify' to create a combined, 'minified' 
 * version.  (See Makefile)
 */
"use strict";
var moment = require('./node_modules/moment');
var daterangepicker = require('./node_modules/bootstrap-daterangepicker');

/* Export to global environment */ 
window.moment = moment;
window.daterangepicker = daterangepicker;

