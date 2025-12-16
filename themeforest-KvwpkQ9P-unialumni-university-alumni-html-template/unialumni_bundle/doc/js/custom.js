(function ($) {
	"use strict";


	$(document).ready(function () {
		/* ==============================================
	ANIMATION -->
	=============================================== */

		new WOW({
			boxClass    : 'wow', // default
			animateClass: 'animated', // default
			offset      : 0, // default
			mobile      : true, // default
			live        : true // default
		}).init();

		/* ==============================================
		LIGHTBOX -->
		=============================================== */

		$('a[data-gal]').each(function () {
			$(this).attr('rel', $(this).data('gal'));
		});

		$("a[data-rel^='prettyPhoto']").prettyPhoto({
			animationSpeed : 'slow',
			theme          : 'light_square',
			slideshow      : true,
			overlay_gallery: true,
			social_tools   : false,
			deeplinking    : false
		});

		/* ==============================================
		SCROLL -->
		=============================================== */


		$('a[href*=#]:not([href=#])').click(function () {
			if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
				var target = $(this.hash);
				target     = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
				if (target.length) {
					$('html,body').animate({
						scrollTop: target.offset().top
					}, 1000);
					return false;
				}
			}
		});


		$('body').scrollspy({
			target: '.docs-sidebar'
		});

		$('[data-spy="scroll"]').each(function () {
			var $spy = $(this).scrollspy('refresh')
		})

		/* ==============================================
		VIDEO FIX -->
		=============================================== */

		// Target your .container, .wrapper, .post, etc.
		$(".media").fitVids();


		$('.docs-sidebar>nav>li>a').on('click', function () {
			$('.docs-sidebar>nav>li').removeClass('active');
			$(this).parent().addClass('active');
		});
	});


})(jQuery);
