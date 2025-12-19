/*------------------------------------------------------------------
[Master Javascript]

Project Name: UniAlumni - University Alumni Html Template
Version: 1.2.1
Author: codeboxr
Website: https://codeboxr.com
Last Update: 21.06.2023
-------------------------------------------------------------------*/

"use strict";

//jQuery dom ready
jQuery(document).ready(function ($) {


	// Get current path and find target link
	var path = window.location.pathname.split('/').pop();

	// Account for home page with empty path
	if (path == '') {
		path = 'index.html';
	}

	var target = $('.codeboxr-main-menu li a[href="' + path + '"]');
	// Add active class to target link

	target.parent().addClass('current-menu-item');


	// Offcanvas Menu JS
	$('.burger-menu').on('click', function () {
		$('.canvas-menu-wrapper').toggleClass('open-menu');
		$('body').toggleClass('no-scroll');
	});

	$('.close-menu').on('click', function () {
		$('.canvas-menu-wrapper').removeClass('open-menu');
		$('body').removeClass('no-scroll');
	});

	$('.canvas-menu-content ul li a').on('click', function () {
		$('.canvas-menu-wrapper').removeClass('open-menu');
	}); //end Offcanvas Menu JS

	// Offcanvas Dropdown Menu JS
	function offcanvasDropdownMenu() {
		if ($(window).width() < 991) {
			if (!$('.has-submenu i').length) {
				$('header .has-submenu').append('<i role="button" class="fa fa-angle-down"></i>');
				$('header .has-submenu i').addClass('hide-drop')
			}

			$('header .has-submenu i').on('click', function () {
				if (!$(this).hasClass('animation')) {
					$(this).parent().toggleClass('is-open');
					$(this).addClass('animation');
					$(this).parent().siblings().removeClass('is-open').find('.fa').removeClass('hide-drop').prev('.sub-menu').slideUp(250);
					if ($(this).hasClass('hide-drop')) {
						if ($(this).closest('.sub-menu').length) {
							$(this).removeClass('hide-drop').prev('.sub-menu').slideToggle(250);
						} else {
							$('.has-submenu i').addClass('hide-drop').next('.sub-menu').hide(250);
							$(this).removeClass('hide-drop').prev('.sub-menu').slideToggle(250);
						}
					} else {
						$(this).addClass('hide-drop').prev('.sub-menu').hide(100).find('.has-submenu a').addClass('hide-drop').prev('.sub-menu').hide(250);
					}
				}
				setTimeout(removeClass, 250);

				function removeClass() {
					$('header .codeboxr-main-menu i').removeClass('animation')
				}
			})
		} else {
			$('header .has-submenu i').remove()
		}
	}

	// Window Load
	$(window).on('load', function () {
		offcanvasDropdownMenu();
	});

	window.addEventListener('orientationchange', function () {
		offcanvasDropdownMenu();
	}, false);

	// Window Resize
	$(window).on('resize', function () {
		offcanvasDropdownMenu();
	}); //end Offcanvas Dropdown Menu JS



	// Sticky Header JS
	$(window).on('scroll', function () {
		var scroll = $(window).scrollTop();
		if (scroll < 150) {
			$('.header-fixed').removeClass('showed');
		} else {
			$('.header-fixed').addClass('showed');
		}
	}); //end Sticky Header JS


	//Home Slider  JS
	var $slider_carousel = $('.slider-active-wrap');

	$slider_carousel.on('initialized.owl.carousel', function (event) {
		$('#upcoming-area').show();
	});

	$slider_carousel.owlCarousel({
		items: 1,
		loop: true,
		nav: false,
		autoplay: false,
		autoplayTimeout: 3000,
		animateOut: 'fadeOut',
		animateIn: 'fadeIn'
	}); //end Home Slider  JS

	$slider_carousel.owlCarousel({
		callbacks: true
	});

	$('.social-networks-icon').addClass('social-networks-icon-display');

	//Upcoming Event JS
	$('.upcoming-event-content').owlCarousel({
		nav: true,
		loop: true,
		items: 1,
		dots: false,
		autoPlay: false,
		navText: ["<i class='fas fa-chevron-left'></i>", "<i class='fas fa-chevron-right'></i>"]
	});
	//end Upcoming Event JS

	// Funfact Counter JS
	$('.funfact-count').counterUp({
		delay: 50,
		time: 1000
	}); //end funfact js

	// Gallery Filter JS
	$('.gallery-gird').isotope();

	$(".gallery-menu span").on('click', function () {

		$(".gallery-menu span").removeClass('active');
		$(this).addClass('active');

		var filterValue = $(this).attr('data-filter');
		$(".gallery-gird").isotope({
			filter: filterValue
		});
		return false;
	}); //end gallery js

	// Magnific Image Popup JS
	$('.single-gallery-item').magnificPopup({
		delegate: 'a',
		type: 'image',
		mainClass: 'mfp-fade',
		removalDelay: 300,
		gallery: {
			enabled: true
		}
	});

	// Magnific Video Popup JS
	$('.video-popup').magnificPopup({
		type: 'iframe',
		mainClass: 'mfp-fade',
		removalDelay: 300
	}); //end Magnific Video


	//smooth scrolling
	$('.smooth-scroll').smoothScroll({
		speed: 1000,
		easing: 'swing'
	}); //end smooth scrolling

	//Testimonial JS
	$('.people-to-say-wrapper').owlCarousel({
		nav: false,
		loop: true,
		items: 3,
		dots: false,
		autoPlay: true,
		margin: 30,
		responsive: {
			0: {
				items: 1
			},
			480: {
				items: 1
			},
			768: {
				items: 2
			},
			992: {
				items: 3
			}
		}
	}); //end Testimonial JS

	//Nice select JS
	$('select').niceSelect();

	// Event Details CarouselJS
	$('.event-thumbnail-carousel').owlCarousel({
		items: 1,
		loop: true,
		dots: false,
		nav: true,
		navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>']
	}); //end event carousel

	// Scroll to Top Click
	$('.scroll-top').on('click', function () {
		$('html').animate({
			scrollTop: 0
		}, 2000);

		return false;
	}); //end scroll top click

	//event-countdown-counter
	$('.event-countdown-counter').each(function (index, element) {
		var $element = $(element),
			$date = $element.data('date');

		$element.countdown($date, function (event) {
			var $this = $(this).html(event.strftime(''

				+
				'<div class="counter-item"><span class="counter-label">Days</span><span class="single-cont">%D</span></div>' +
				'<div class="counter-item"><span class="counter-label">Hr</span><span class="single-cont">%H</span></div>' +
				'<div class="counter-item"><span class="counter-label">Min</span><span class="single-cont">%M</span></div>' +
				'<div class="counter-item"><span class="counter-label">Sec</span><span class="single-cont">%S</span></div>'));
		});


	});

	//All Window Srcoll Function
	$(window).scroll(function () {
		//Scroll top Hide Show
		if ($(window).scrollTop() >= 500) {
			$('.scroll-top').fadeIn();
		} else {
			$('.scroll-top').fadeOut();
		}

	}); //end all Window Srcoll Function


	//Local PATH
	var cbx_path = window.location.protocol + '//' + window.location.host;
	var pathArray = window.location.pathname.split('/');
	for (var i = 1; i < (pathArray.length - 1); i++) {
		cbx_path += '/';
		cbx_path += pathArray[i];
	}

	//Start Contact Form Validation And Ajax Submission

	var $contactForm = $('form#cbx-contact-form');
	$contactForm.validate({
		submitHandler: function (form) {
			var $this_form = $(form);
			$.ajax({
				url: cbx_path + '/php/contact.php',
				type: 'post',
				data: $this_form.serialize(),
				success: function (response) {

					try {
						var response = $.parseJSON(response);

						//if validation error
						if (response.validation_error) {
							//for field error
							$.each(response.error_field, function (i) {
								if ($('label#' + response.error_field[i] + '-error').length == 0) {
									$('#' + response.error_field[i]).after('<label class="error" for="' + response.error_field[i] + '" id="' + response.error_field[i] + '-error"></label>');
								}
								$('label#' + response.error_field[i] + '-error').text(response.message[response.error_field[i]]);
							});
						} else {
							if (response.error) {
								$('#cbx-formalert').addClass("alert alert-danger").html(response.successmessage);
								new AWN().alert('Something is wrong. Message sending failed!', {
									durations: {
										success: 0
									}
								});
							} else {
								$('#cbx-formalert').addClass("alert alert-success").html(response.successmessage);

								new AWN().success('Message sent successfully', {
									durations: {
										success: 0
									}
								});
							}

							$this_form[0].reset();
						}

					} catch (e) {
						$this_form[0].reset();
					}
				},
				error: function (error) {

					$this_form[0].reset();
				}
			});

			return false;

		},

		rules: {
			'cbxname': {
				required: true
			},
			'cbxemail': {
				required: true,
				email: true
			},
			'cbxmessage': {
				required: true
			},
			'cbxsubject': {
				required: true
			}
		}
	}); //End Contact Form js


	//Email Subscription Validation And Ajax Submission
	var $subscribeForm = $('form#cbx-subscribe-form');

	$subscribeForm.validate({
		submitHandler: function (form) {
			var $this_form = $(form);
			$.ajax({
				url: cbx_path + '/php/subscribe.php',
				type: 'post',
				data: $this_form.serialize(),
				success: function (response) {
					$this_form.find('cbx-subscribe-form-error').html('');

					try {
						var response = $.parseJSON(response);

						//if validation error
						if (response.validation_error) {
							$this_form.find('#cbx-subscribe-form-error').html('<label id="subscribe-error" class="error" for="subscribe">' + response.message.email + '</label>');
						} else {
							//no validation error but there can be email sending email
							if (response.error) {
								$this_form.find('#cbx-subscribe-form-error').html('<label id="subscribe-error" class="error" for="subscribe">' + response.successmessage + '</label>');
							} else {
								$this_form.find('#cbx-subscribe-form-error').html('<label id="subscribe-success" class="success" for="subscribe">' + response.successmessage + '</label>');
							}

							$this_form[0].reset();
						}
					} catch (e) {
						$this_form[0].reset();
					}
				},
				error: function (error) {
					$this_form[0].reset();
				}
			});

			return false;

		},

		errorPlacement: function (error, element) {
			console.log('dd', element.attr("name"))
			if (element.attr("name") == "email") {
				//error.appendTo("#cbx-subscribe-form-error");
				$('#cbx-subscribe-form-error').html(error);
			} else {
				error.insertAfter(element)
			}
		},
		rules: {
			'email': {
				required: true,
				email: true
			},

		}
	}); //End Subscription



	//End Email Subscription Validation And Ajax Submission


	$(document).ready(function () {
		$('.dropdown-menu a.dropdown-toggle').on('click', function (e) {
			var $el = $(this);
			var $parent = $(this).offsetParent(".dropdown-menu");
			if (!$(this).next().hasClass('show')) {
				$(this).parents('.dropdown-menu').first().find('.show').removeClass("show");
			}
			var $subMenu = $(this).next(".dropdown-menu");
			$subMenu.toggleClass('show');

			$(this).parent("li").toggleClass('show');

			$(this).parents('li.nav-item.dropdown.show').on('hidden.bs.dropdown', function (e) {
				$('.dropdown-menu .show').removeClass("show");
			});

			if (!$parent.parent().hasClass('navbar-nav')) {
				$el.next().css({
					"top": $el[0].offsetTop,
					"left": $parent.outerWidth() - 4
				});
			}

			return false;
		});
	});

});