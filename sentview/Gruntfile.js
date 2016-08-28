module.exports = function(grunt) {
	var target = grunt.option('target') || 'dev';
	var isDev = target == 'dev';
	
	var cacheString = Math.round((new Date()).getTime()/1000);
	var libCacheString = '0.0.1';
	
	grunt.initConfig({
		template: {
			any: {
				options: {
					data: {
						cacheString: cacheString,
						libCacheString: libCacheString
					}
				},
				files: {
					'dashboard/templates/build/index.html': 'dashboard/templates/src/index.html'
				}
			}
		},
		uglify: {
			lib: {
				options: {
					mangle: false,
					beautify: isDev
				},
				files: {
					'client/build/js/lib.js': ['node_modules/angular/angular.js', 'node_modules/d3/build/d3.js']
				}
			},
			app: {
				options: {
					mangle: false,
					sourceMap: isDev,
					sourceMapName: 'client/build/js/app.map',
					beautify: isDev
				},
				files: {
					'client/build/js/app.js': ['client/js/app/_declarations.js','client/js/app/**/*.js']
				}
			}
		},
		sass: {
			any: {
				files: {
					'client/build/css/site.css': 'client/styles/site.scss'
				}
			}
		},
		watch: {
			options: { spawn: false },
			app: {
				files: ['client/js/**'],
				tasks: ['uglify:app']
			},
			templates: {
				files: ['dashboard/templates/src/**'],
				tasks: ['template']
			},
			sass: {
				files: ['client/styles/**'],
				tasks: ['sass']
			}
		}
	});
	
	grunt.loadNpmTasks('grunt-contrib-uglify');
	grunt.loadNpmTasks('grunt-contrib-watch');
	grunt.loadNpmTasks('grunt-contrib-sass');
	grunt.loadNpmTasks('grunt-template');
	
	grunt.registerTask('default', ['uglify', 'template', 'sass']);
}
