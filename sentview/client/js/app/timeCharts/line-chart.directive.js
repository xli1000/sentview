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
			link: linkSvLineChart
		};
	}
	
	function linkSvLineChart(scope, el, attrs, controller) {	
		var initialized = false;			
		scope.$watch('vm.series', function() {
			if (controller.series && controller.series.length > 0) {
				if (!initialized) {
					initialize(controller.series);
					initialized = true;
				}
				rerender(controller.series);
			}
		}, true);
		
		var margin = { top: 10, right: 20, bottom: 30, left: 40 };
		var fullWidth = 1000; //viewBox pixels
		var fullHeight = Math.round(fullWidth/parseFloat(controller.aspectRatio));
		var width = fullWidth - margin.left - margin.right;
		var height = fullHeight - margin.top - margin.bottom;
		var x;
		var y;
		var xAxis;
		var yAxis;
		var xAxisEl;
		var yAxisEl;
		var seriesLine;
		var chartArea;
		var seriesLinePath;
		var averageLinePath;
		var currentPoint;
		var valueLabel;
		
		var svg = d3.select(el[0])
			.append('svg')
			.classed('line-chart', true)
			.classed('svg-content', true)
			.attr('viewBox', '0 0 ' + fullWidth  +' ' + fullHeight)
			.attr('preserveAspectRatio', 'xMidYMin meet');
		
		
		function rerender(series) {
			
			x.domain(d3.extent(series, function(d) { return d.ts * 1000; }));
			var yExtent = d3.extent(series, function(d) { return d.score; });
			
			y.domain(yExtent);
				
			xAxisEl
				.call(xAxis);
			yAxisEl
				.call(yAxis);
			
			averageLinePath
				.attr('y1', y(controller.average))
				.attr('y2', y(controller.average));
			
			seriesLinePath
				.datum(series)
				.attr('d', seriesLine);
			
			currentPoint
				.attr('cx', x(series[series.length-1].ts * 1000))
				.attr('cy', y(series[series.length-1].score))
				.style('opacity', '0')
				.transition()
				.style('opacity', '100')
				.duration(670);
			
			valueLabel
				.text(d3.format('.5f')(series[series.length-1].score));
		}
		
		function initialize(series) {
			
			x = d3.scaleTime();
			y = d3.scaleLinear();
	
			x.range([0, width]);
			y.range([height, 0]);
			
			seriesLine = d3.line()
				.x(function(d) { return x(d.ts * 1000); })
				.y(function(d) { return y(d.score); });
			
			chartArea = 
				svg.append('g')
					.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
			
			seriesLinePath = chartArea.append('path')
				.attr('class', 'line');
			
			xAxis = d3.axisBottom()
				.scale(x);
				
			yAxis = d3.axisLeft()
				.scale(y)
				.ticks(6);
				
			xAxisEl = chartArea.append('g')
				.attr('class', 'x axis')
				.attr('transform', 'translate(0,' + height + ')');
			
			yAxisEl = chartArea.append('g')
				.attr('class', 'y axis');
			
			averageLinePath = chartArea.append('line')
				.attr('class', 'average-line')
				.attr('x1', 0)
				.attr('x2', width);
			
			currentPoint = chartArea.append('circle')
				.attr('class', 'current-point');
				
			valueLabel = chartArea.append('text')
				.attr('x', width)
				.attr('y', 10)
				.attr('text-anchor', 'end');
		}
	}
	
}());
