// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('datacard_compare', function ($) {
  return {
    initialize: function () {
      console.log("I've been initialized for element: ", this.el);
	
      // proxyAll() ensures that whenever an _on*() function from this
      // JavaScript module is called, the `this` variable in the function will
      // be this JavaScript module object.
      //
      // You probably want to call proxyAll() like this in the initialize()
      // function of most modules.
      //
      // This is a shortcut function provided by CKAN, it wraps jQuery's
      // proxy() function: http://api.jquery.com/jQuery.proxy/
      $.proxyAll(this, /_on/);

      // Add a Bootstrap popover to the button. Since we don't have the HTML
      // from the snippet yet, we just set the content to "Loading..."
      this.el.popover({title: this.options.title, html: true,
                       content: this._('Loading...'), placement: 'right'});

      // Add an event handler to the button, when the user clicks the button
      // our _onClick() function will be called.
      this.el.on('click', this._onClick);

      // Subscribe to 'dataset_popover_clicked' events.
      // Whenever any line of code publishes an event with this topic,
      // our _onPopoverClicked function will be called.
      this.sandbox.subscribe('compare_clicked',
                             this._onPopoverClicked);
    },

    teardown: function() {
      this.sandbox.unsubscribe('compare_clicked',
                               this._onPopoverClicked);
    },

    // Whether or not the rendered snippet has already been received from CKAN.
    _snippetReceived: false,

    _onClick: function(event) {

        // Grab selected datasets
        var checkboxes = document.querySelectorAll(`input[name="check"]:checked`); // getElementsByClassName("dcstyle-check");
        let values = []
        for (let i = 0; i < checkboxes.length; i++) {
          var grabbed = checkboxes[i].value.split("check-")[1];
          console.log("Checked value: " + grabbed);
          values.push(grabbed);
        }
        if (values.length < 2) {
          alert("Please select at least two datasets to compare");
          this.el.popover('destroy');
          var compareEl = document.getElementById("compare");
          // console.log("Compare element found: " + compareEl);
          compareEl.innerHTML = "";
          return;
        } else {
          let selected = []
          //console.log("Original packages: " + this.options.packages[0]);
          //for(let i = 0; i < Object.values(this.options).length; i++) {
            //console.log("Looking for: " + Object.keys(this.options)[i]);
            //if (values.includes(p[name])) {
              //selected.push(p);
            //}
          //}
          var param = {packages: values};
          this.options.packages = JSON.stringify(values);
          console.log("Passing packages: " + this.options.packages);
        
          // Send an ajax request to CKAN to render the popover.html snippet.
          // We wrap this in an if statement because we only want to request
          // the snippet from CKAN once, not every time the button is clicked.
          if (!this._snippetReceived) {
            this.sandbox.client.getTemplate('datacard_compare.html',
                                            this.options, 
                                            this._onReceiveSnippet);
            //HACK: Disabling this temporarily
            //this._snippetReceived = true;
          }
        }

        // Publish a 'dataset_popover_clicked' event for other interested
        // JavaScript modules to receive. Pass the button that was clicked as a
        // parameter to the receiver functions.
        this.sandbox.publish('compare_clicked', this.el);
    },

    // This callback function is called whenever a 'dataset_popover_clicked'
    // event is published.
    _onPopoverClicked: function(button) {

      // Wrap this in an if, because we don't want this object to respond to
      // its own 'dataset_popover_clicked' event.
      if (button != this.el) {

        // Hide this button's popover.
        // (If the popover is not currently shown anyway, this does nothing).
        this.el.popover('hide');
      }
    },

     // CKAN calls this function when it has rendered the snippet, and passes
    // it the rendered HTML.
    _onReceiveSnippet: function(content) {
	// Replace the popover with a new one that has the rendered HTML from the
	// snippet as its contents.
	this.el.popover('destroy');

        var compareEl = document.getElementById("compare");
        // console.log("Compare element found: " + compareEl);
        compareEl.innerHTML = content;
        // this.el.disabled = true;
     
	// this.el.popover({title: "Comparing search results", html: true,
	//		 content: content, placement: 'right'});
	// this.el.popover('show');
    },
  };
});

ckan.module('datacard_popover', function ($) {
  return {
    initialize: function () {
      console.log("I've been initialized for element: ", this.el);
	
      // proxyAll() ensures that whenever an _on*() function from this
      // JavaScript module is called, the `this` variable in the function will
      // be this JavaScript module object.
      //
      // You probably want to call proxyAll() like this in the initialize()
      // function of most modules.
      //
      // This is a shortcut function provided by CKAN, it wraps jQuery's
      // proxy() function: http://api.jquery.com/jQuery.proxy/
      $.proxyAll(this, /_on/);

      // Add a Bootstrap popover to the button. Since we don't have the HTML
      // from the snippet yet, we just set the content to "Loading..."
      //this.el.popover({title: this.options.title, html: true,
        //               content: this._('Loading...'), placement: 'right'});

      // Add an event handler to the button, when the user clicks the button
      // our _onClick() function will be called.
      this.el.on('click', this._onClick);

      // Subscribe to 'dataset_popover_clicked' events.
      // Whenever any line of code publishes an event with this topic,
      // our _onPopoverClicked function will be called.
      this.sandbox.subscribe('dataset_popover_clicked',
                             this._onPopoverClicked);
    },

    teardown: function() {
      this.sandbox.unsubscribe('dataset_popover_clicked',
                               this._onPopoverClicked);
    },

    // Whether or not the rendered snippet has already been received from CKAN.
    _snippetReceived: false,

    _onClick: function(event) {

        // Send an ajax request to CKAN to render the popover.html snippet.
        // We wrap this in an if statement because we only want to request
        // the snippet from CKAN once, not every time the button is clicked.
        if (!this._snippetReceived) {
            this.sandbox.client.getTemplate('datacard_popover.html',
                                            this.options,
                                            this._onReceiveSnippet);
            this._snippetReceived = true;
        }

        // Publish a 'dataset_popover_clicked' event for other interested
        // JavaScript modules to receive. Pass the button that was clicked as a
        // parameter to the receiver functions.
        this.sandbox.publish('dataset_popover_clicked', this.el);
    },

    // This callback function is called whenever a 'dataset_popover_clicked'
    // event is published.
    _onPopoverClicked: function(button) {

      // Wrap this in an if, because we don't want this object to respond to
      // its own 'dataset_popover_clicked' event.
      if (button != this.el) {

        // Hide this button's popover.
        // (If the popover is not currently shown anyway, this does nothing).
        this.el.popover('hide');
      }
    },

     // CKAN calls this function when it has rendered the snippet, and passes
    // it the rendered HTML.
    _onReceiveSnippet: function(content) {
	// Replace the popover with a new one that has the rendered HTML from the
	// snippet as its contents.
	//this.el.popover('destroy');
	this.el.popover({title: this.options.title, html: true,
			 content: content, placement: 'right'});
	this.el.popover('show');
    },
  };
});
