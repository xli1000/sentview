(function() {
	angular
		.module('sentview.termCharts')
		.directive('svTermCloud', svTermCloud);
	
	svTermCloud.$inject = ['$window'];

	function svTermCloud($window) {
		return {
			restrict: 'E',
			scope: {},
			controller: function() {},
			bindToController: { 
				aspectRatio: '@',
				terms: '='
			},
			controllerAs: 'vm',
			link: linkSvTermCloud
		};

		function linkSvTermCloud(scope, el, attrs, controller) {
			var TWITTER_SEARCH_URL = 'https://twitter.com/search?q=';
			var TWITTER_HASHTAG_URL = 'https://twitter.com/hashtag/';

			var margin = { top: 0, right: 5, bottom: 0, left: 5 };
			var fullWidth = 1000; //viewBox pixels
			var minFontSize = 15;
			var maxFontSize = 45;
			var fullHeight = Math.round(fullWidth/parseFloat(controller.aspectRatio));
			var width = fullWidth - margin.left - margin.right;
			var height = fullHeight - margin.top - margin.bottom;
			var svg;
			var layout;
			var chartArea;
			var fontSizeScale;
			var initialized = false;

			scope.$watch('vm.terms', function() {
				if (_.size(controller.terms)!==0) {
					if (!initialized) {
						initialize();
					}
					rerender();
				}
			});

			function transformedTerms() {
				var termsArray = [];
				_.forIn(controller.terms, function(score, term) {
					termsArray.push({ term: term, score: score })
				});
				return termsArray;
			}

			function calculateScale() {
				var min = d3.min(d3.values(controller.terms));
				var max = d3.max(d3.values(controller.terms));

				fontSizeScale = d3.scaleLinear()
					.domain([min, max])
					.range([minFontSize, maxFontSize]);

				layout
					.fontSize(function(d) { return fontSizeScale(d.score); })
					.text(function(d) { return d.term });
			}

			function initialize() {
				svg = d3.select(el[0])
					.append('svg')
					.attr('viewBox', '0 0 ' + fullWidth  +' ' + fullHeight)
					.attr('preserveAspectRatio', 'xMidYMin meet')
					.classed('svg-content', true)
					.classed('term-chart', true);

				chartArea = svg.append('g')
					.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
			}

			function rerender() {
				layout = d3.layout.cloud()
					.size([width, height])
					.words(transformedTerms())
					.padding(10)
					.spiral('rectangular')
					.rotate(function() {return 0})
					.on('end', draw);

				calculateScale();

				layout.start();
			}

			function draw(terms) {
				chartArea
					.selectAll('text', 'term')
					.data(terms)
					.enter()
					.append('text')
					.attr('class', 'term')
					.text(function(d) { return d.term; })
					.style('font-size', function(d) { return fontSizeScale(d.score) + 'px'; })
					.style('text-anchor', 'middle')
					.attr("transform", function(d) {
				        return "translate(" + [d.x, d.y] + ")";
				     })
					.call(addHandlers);
			}

			function addHandlers(elements) {
				elements.on('click', onClickTerm);

				function onClickTerm(d) {
					var url;
					if (d.term.charAt(0) === '#') {
						url = TWITTER_HASHTAG_URL + encodeURIComponent(d.term.slice(1));
					} else {
						url = TWITTER_SEARCH_URL + encodeURIComponent(d.term);
					}

					$window.open(url);
				}
			}
		}
	}
}());