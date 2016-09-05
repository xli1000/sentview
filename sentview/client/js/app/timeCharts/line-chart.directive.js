(function() {
	angular
		.module('sentview.timeCharts')
		.directive('svLineChart', svLineChart);
	
	function svLineChart() {
		return {
			restrict: 'E',
			scope: {},
			controller: function() {},
			bindToController: { 
				series: '=', 
				aspectRatio: '@',
				average: '='
			},
			controllerAs: 'vm',
			link: function(scope, el, attrs, controller) {				
				scope.$watch('vm.series', function() {
					if (controller.series) {
						render(controller.series);
					}
				}, true);
				
				var margin = { top: 10, right: 20, bottom: 30, left: 40 };
				var fullWidth = 1000; //viewBox pixels
				var fullHeight = Math.round(fullWidth/parseFloat(controller.aspectRatio));
				var width = fullWidth - margin.left - margin.right;
				var height = fullHeight - margin.top - margin.bottom;
				
				var svg = d3.select(el[0])
					.append('svg')
					.classed('line-chart', true)
					.classed('svg-content', true)
					.attr('viewBox', '0 0 ' + fullWidth  +' ' + fullHeight)
					.attr('preserveAspectRatio', 'xMidYMin meet');
				
					
				function render(series) {
					
					var x = d3.scaleTime();
					var y = d3.scaleLinear();
					
					x.domain(d3.extent(series, function(d) { return d.ts * 1000; }));
					var extent = d3.extent(series, function(d) { return d.score; });
					
					y.domain(extent);
				
			
					x.range([0, width]);
					y.range([height, 0]);
					
					var xAxis = d3.axisBottom()
						.scale(x);
						
					var yAxis = d3.axisLeft()
						.scale(y);
						
					var seriesLine = d3.line()
						.x(function(d) { return x(d.ts * 1000); })
						.y(function(d) { return y(d.score); });
					
					var chartArea = 
						svg.append('g')
							.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
					
					chartArea.append('path')
						.datum(series)
						.attr('class', 'line')
						.attr('d', seriesLine);
						
					chartArea.append('g')
						.attr('class', 'x axis')
						.attr('transform', 'translate(0,' + height + ')')
						.call(xAxis);
					
					chartArea.append('g')
						.attr('class', 'y axis')
						.call(yAxis);
					
					//average line
					chartArea.append('line')
						.attr('class', 'average-line')
						.attr('x1', 0)
						.attr('y1', y(controller.average))
						.attr('x2', width)
						.attr('y2', y(controller.average));
						
					
				}
			}
		};
	}
	
})();
