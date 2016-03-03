$(document).ready(function(){
    require(["esri/map","esri/geometry/Extent", "esri/SpatialReference", "esri/layers/ArcGISTiledMapServiceLayer", "esri/layers/ArcGISDynamicMapServiceLayer", "esri/tasks/IdentifyTask", "esri/tasks/IdentifyParameters", "esri/toolbars/draw", "esri/symbols/SimpleLineSymbol", "esri/symbols/SimpleFillSymbol", "dojo/dom", "dojo/on", "dojo/request", "dojo/_base/Color", "esri/graphic", "esri/tasks/query", "esri/tasks/QueryTask", "esri/dijit/Geocoder","dojo/domReady!"],
    function (Map, Extent, SpatialReference, ArcGISTiledMapServiceLayer, ArcGISDynamicMapServiceLayer, IdentifyTask, IdentifyParameters, Draw, SimpleLineSymbol, SimpleFillSymbol, dom, on, request, Color, Graphic, Query, QueryTask, Geocoder) {
    
        String.prototype.replaceAll = function(str1, str2, ignore) {
    	   return this.replace(new RegExp(str1.replace(/([\/\,\!\\\^\$\{\}\[\]\(\)\.\*\+\?\|\<\>\-\&])/g,"\\$&"),(ignore?"gi":"g")),(typeof(str2)=="string")?str2.replace(/\$/g,"$$$$"):str2);
    	};
    	
    	var sr = new SpatialReference({wkid: 26910});
    	
    	var map = new Map("map", {
    		logo: false,
    		extent: new Extent({
    			"xmin": 505000,
    			"ymin": 5428000,
    			"xmax": 523000,
    			"ymax": 5452000,
    			extent: sr
    		})
    	});
    	
    	var dataFormat, currentlayerId, currentLayer, scale;
    	var geocoder;
    	var packageTrue;
    	var tb;
    	var xmin, xmax, ymin, ymax;
    
    	var baseMap = new ArcGISTiledMapServiceLayer("http://cosmos.surrey.ca/COSREST/rest/services/Base_Map_All_Scales/MapServer");
    	var allLayers = new ArcGISDynamicMapServiceLayer("http://cosmos.surrey.ca/COSREST/rest/services/OpenData/MapServer");
    	var roadNamesLayer = new ArcGISDynamicMapServiceLayer("http://cosmos.surrey.ca/COSREST/rest/services/RoadNames/MapServer");
    	var identifyTask = new IdentifyTask("http://cosmos.surrey.ca/COSREST/rest/services/OpenData/MapServer");
    	var identifyParams = new IdentifyParameters();
    
    	var query = new Query();
    	query.returnGeometry = true;
    	query.outFields = ["OBJECTID"];
    	query.where = "1=1";
    
    	var symbol = new SimpleFillSymbol(SimpleFillSymbol.STYLE_SOLID, new SimpleLineSymbol(SimpleLineSymbol.STYLE_DASHDOT, new Color([255,0,0]), 3), new Color([255,215,0,0.5]));
    
    	var options = {
    		valueNames: ['field', 'attribute']
    	};
    
    	var attribList = new List('attributeInspector', options);
    	
    	map.addLayers([baseMap, allLayers, roadNamesLayer]);
    	roadNamesLayer.setVisibleLayers([0,1,2,3]);
    	allLayers.on("load", function () {
    		getlayerId(getParameterByName('layername'));
    	});
    
    	map.on("click", function (evt) {
    		doIdentify(evt);
    	});
    
    	map.on("load", initToolbar);
    	map.on("load", function(){
    		var dldata = dom.byId("dldata");
    		on(dldata, "click", finished);
    	});
    
    	geocoder = new Geocoder({
    		map: map,
    		autoComplete: true,
    		minCharacters: 3
    	}, "search");
    
    	geocoder.startup();
    	var geocoderInput = document.getElementById('search_input');
    	geocoderInput.onclick = function () {
    		geocoderInput.val = '';
    	};
        
        $('#search').css('top', 'auto');
    
    	function initToolbar() {
    
    		tb = new Draw(map, {showTooltips: true});
    		tb.on("draw-end", addGraphic);
    
    		on(dom.byId("drawABox"), "click", function (evt) {
    			map.graphics.clear();
    			map.disableMapNavigation();
    			tb.activate(Draw.RECTANGLE);
    		});
    	}
    
    	function addGraphic(evt) {
    		tb.deactivate();
    		map.enableMapNavigation();
    		var ext = evt.geometry.getExtent();
    		// round to 6 decimal places
    		xmin = Math.round(ext.xmin);
    		ymin = Math.round(ext.ymin);
    		xmax = Math.round(ext.xmax);
    		ymax = Math.round(ext.ymax);
    
    		map.graphics.add(new Graphic(evt.geometry, symbol));
    	}
    
    	function getlayerId(layerName) {
    		//code to zoom to vicinity of data
    		layerName = layerName.replaceAll("-"," ");
    		layerName = camelCase(layerName);
    
    		function camelCase(s) {
    			return (s||'').toLowerCase().replace(/(\b|-)\w/g, function(m) {
    				return m.toUpperCase();
    			});
    		}
    				
    		dataFormat = getParameterByName('dataformat');
    				
    		if (layerName) {
    			var n = layerName.indexOf("Ortho");
    			var o = layerName.indexOf("Satellite");
    			var p = layerName.indexOf("Grid");
    			var q = layerName.indexOf("Hillshade");
    			var r = layerName.indexOf("Raw");
    
    			if (n != -1 || o != -1){
    
    				var allOrthos = new ArcGISDynamicMapServiceLayer("http://cosmos.surrey.ca/COSREST/rest/services/AerialImages/MapServer");
    				map.removeLayer(allLayers);
    				map.removeLayer(roadNamesLayer);
    				map.addLayer(allOrthos);
    				map.addLayer(roadNamesLayer);
    				roadNamesLayer.setVisibleLayers([0,1,2,3]);
    				
    				switch(layerName){
    				
    					case "1998 Orthophoto" : allOrthos.setVisibleLayers([30]); break;
    					case "2001 Orthophoto" : allOrthos.setVisibleLayers([29]); break;
    					case "2003 Satellite" : allOrthos.setVisibleLayers([28]); break;
    					case "2004 Orthophoto" : allOrthos.setVisibleLayers([23]); break;
    					case "2005 Orthophoto" : allOrthos.setVisibleLayers([18]); break;
    					case "2006 Orthophoto" : allOrthos.setVisibleLayers([13]); break;
    					case "2007 Orthophoto" : allOrthos.setVisibleLayers([8]); break;
    					case "2008 Orthophoto" : allOrthos.setVisibleLayers([7]); break;
    					case "2009 Orthophoto" : allOrthos.setVisibleLayers([6]); break;							
    					case "2010 Orthophoto" : allOrthos.setVisibleLayers([5]); break;
    					case "2011 Orthophoto" : allOrthos.setVisibleLayers([4]); break;
    					case "2012 Orthophoto" : allOrthos.setVisibleLayers([3]); break;					
    					case "2013 Orthophoto" : allOrthos.setVisibleLayers([2]); break;
    					case "2014 Orthophoto" : allOrthos.setVisibleLayers([1]); break;
    					case "2015 Orthophoto" : allOrthos.setVisibleLayers([0]); break;
    
    					default: break;
    
    				}
    				return;	
    			}
    		
    			var layerInfos = allLayers.layerInfos;
    			var availability = "";
    			layerName = layerName.toLowerCase();
    			
    			var il = layerInfos.length;
    			for (var i = 0; i < il; i++) {
    				var templayerName = layerInfos[i].name;
    				templayerName = templayerName.toLowerCase();
    
    				if (templayerName == layerName) {
    
    					currentlayerId = layerInfos[i].id;
    					scale = layerInfos[i].minScale;
    					
    					//test to see if this is a layer package
    					packageTrue = layerName.indexOf("package");
    											
    					if (packageTrue == -1){
    						allLayers.setVisibleLayers([currentlayerId]);
    					}
    
    					if (scale > 0) {
    						scale = scale - 1;
    						alert("FYI: " + layerName + " is only viewable at 1: " + scale + "  Map will automatically zoom to viewable scale.");
    						map.setScale(scale);
    					}
    					
    					if (layerName != 'road surface' && packageTrue === -1){
    						var queryTask = new QueryTask("http://cosmos.surrey.ca/COSREST/rest/services/OpenData/MapServer/" + currentlayerId);
    						queryTask.execute(query, showResults, function(err){
    							console.log(err);
    						});
    					}
    
    					availability = "yep";
    				}
    			}
    							
    			if (r != -1 ){
    				availability = "yep";
    			}
    			 
    			var test = layerName.indexOf("contour");
    			if (availability == "" ){
    				if (availability == "" && test != 0){
    					alert("Sorry, this layer is not available for download via the map.  Please click back and select the \"Download File\" option.");
    				}
    			}
    		}
    	}
    
    	function showResults(featureSet) {
    		var zoomGraphic;
    		var resultFeatures = featureSet.features;
    
    		if (resultFeatures.length < 1000) {
    			var il = resultFeatures.length;
    			for (var i = 0; i < il; i++) {
    				zoomGraphic = resultFeatures[0];
    			}
    
    			var extent = zoomGraphic.geometry.getExtent();
    
    			var newExtent = new Extent(extent.xmin, extent.ymin, extent.xmax, extent.ymax, sr);
    			
    			map.setExtent(newExtent);
    		}
    	}
    
    	function doIdentify(evt) {
    
    		map.graphics.clear();
    		attribList.clear();
    		currentLayer = getParameterByName('layername');
    		currentLayer = currentLayer.replace('-', " ");
    		//code to stop identifying on rasters.
    		var n = currentLayer.toUpperCase().indexOf("ORTHO");
    		var o = currentLayer.toUpperCase().indexOf("SATELLITE");
    
    		if (n == -1 && o == -1) {
    			identifyParams.geometry = evt.mapPoint;
    			identifyParams.mapExtent = map.extent;
    			identifyParams.tolerance = 5;
    			identifyParams.layerIds = [currentlayerId];
    			identifyParams.layerOption = IdentifyParameters.LAYER_OPTION_ALL;
    
    			identifyTask.execute(identifyParams, function (idResults) {
    
    				var attributeInspectorDIV = document.getElementById('attributeInspector');
    				attributeInspectorDIV.style.display = 'block';
    
    				var header = document.getElementById("header");
    				header.innerHTML = "Found " + idResults.length + " " + currentLayer;
    
    				var il = idResults.length;
    				for (var i = 0; i < il; i++) {
    
    					var test = idResults[i].feature.attributes;
    
    					for (var att in test) {
    
    						if (att && test[att] != 'Null') {
    
    							var attUp = att.toUpperCase();
    							if (attUp != "OBJECTID" && attUp != "SHAPE") {
    
    								var aValue = test[att];
    								if (attUp == "SHAPE.AREA" || attUp == "SHAPE_AREA") {
    									att = "AREA";
    								} 
    								else if (attUp == "SHAPE.LENGTH" || attUp == "SHAPE_LENGTH" || attUp == "SHAPE.LEN" || attUp == "SHAPE_LEN") {
    									att = "LENGTH";
    								}
    
    								if (aValue.indexOf("http:") != -1) {
    									aValue = "<a href=\"" + aValue + "\" target= \"_newtab\">More Information</a>";
    								}
    
    								attribList.add({
    									field: '<strong>' + att + ':</strong>',
    									attribute: aValue
    								});
    							}
    						}
    					}
    					
    					attribList.add({
    						field: '=======================',
    						attribute: ''
    					});
    				}
    			},
    			function(err){
    				console.log(err);
    			});
    		}
    	}
    	
    	function getParameterByName(name) {
    		var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    		return match ? decodeURIComponent(match[1].replace(/\+/g, ' ')) : null;
    	}
    	
    	function finished() {
    	
    		var layerType, requestURL, test;
    
    		if (typeof xmin == "undefined") {
    			alert("Please draw a box over the area you wish to download data for.");
    			return;
    		}
    
    		var txtEmail = document.getElementById('txtEmail').value;
    
    		if (txtEmail == "") {
    			alert("Please enter your email address then click Download Data.");
    			return;
    		}
    
    		test = echeck(txtEmail);
    
    		dataFormat = getParameterByName('dataformat');
    
    		if (dataFormat == "json"){dataFormat = "GEOJSON";}
    		if (dataFormat == "dwg"){dataFormat = "ACAD";}
    		if (dataFormat == "csv"){dataFormat = "CSV";}
    		if (dataFormat == "fgdb"){dataFormat = "FILEGDB";}
    		if (dataFormat == "kml"){dataFormat = "OGCKML";}
    		if (dataFormat == "tiff"){dataFormat = "TIFF";}
    
    		var sdeLayer = getParameterByName('layername');
    		
    		sdeLayer = sdeLayer.replaceAll("-"," ");
    		
    		var n = sdeLayer.indexOf("ortho"); if (n != -1) {layerType = "ortho";}
    		var o = sdeLayer.indexOf("satellite");  if (o != -1) {layerType = "satellite";}
    		var p = sdeLayer.indexOf("grid");  if (p != -1) {layerType = "grid";}
    		var q = sdeLayer.indexOf("hillshade");  if (q != -1) {layerType = "hillshade";}
    		var r = sdeLayer.indexOf("raw");  if (r != -1) {layerType = "raw";}
    		
    		if (typeof layerType == "undefined")( layerType = "");
    		
    		switch(layerType){
    			
    			case "ortho" 		: requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/OpenDataRasterDownloader.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&LAYERNAME=" + sdeLayer + "&FORMAT=" + dataFormat + "&FME_SERVER_DEST_DIR=%5C%5Cvagisfme%5CFMEServer%5CData&opt_showresult=false&opt_servicemode=async&opt_requesteremail=" + txtEmail;		break;
    			case "satellite": requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/OpenDataRasterDownloader.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&LAYERNAME=" + sdeLayer + "&FORMAT=" + dataFormat + "&FME_SERVER_DEST_DIR=%5C%5Cvagisfme%5CFMEServer%5CData&opt_showresult=false&opt_servicemode=async&opt_requesteremail=" + txtEmail;		break;
    			case "grid"			: requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/OpenDataRasterDownloader.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&LAYERNAME=" + sdeLayer + "&FORMAT=" + dataFormat + "&FME_SERVER_DEST_DIR=%5C%5Cvagisfme%5CFMEServer%5CData&opt_showresult=false&opt_servicemode=async&opt_requesteremail=" + txtEmail;    break;
    			case "hillshade": requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/OpenDataRasterDownloader.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&LAYERNAME=" + sdeLayer + "&FORMAT=" + dataFormat + "&FME_SERVER_DEST_DIR=%5C%5Cvagisfme%5CFMEServer%5CData&opt_showresult=false&opt_servicemode=async&opt_requesteremail=" + txtEmail;    break;
    			case "raw"		: requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/LidarDownloader.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&FME_SERVER_DEST_DIR=%5C%5Cvagisfme%5CFMEServer%5CData&opt_showresult=false&opt_servicemode=async&opt_requesteremail=" + txtEmail;    break;
    			default: requestURL = "http://gis.surrey.ca:8080/fmedatadownload/DynamicDataDownload/DynamicDataDownload.fmw?MAXX=" + xmax + "&MAXY=" + ymax + "&MINY=" + ymin + "&MINX=" + xmin + "&LAYERNAME=" + sdeLayer + "&FORMAT=" + dataFormat + "&opt_servicemode=async&opt_requesteremail=" + txtEmail; break;
    		}
    
    		var zoomlevel = map.getZoom();
    		if (zoomlevel <=2 && layerType == "ortho"){
    			alert("This extent is too large to download Ortho Imagery.  Please zoom in more and draw a new box.");
    			return;
    		}
    		
    		if (zoomlevel <=4 && layerType == "raw"){
    			alert("This extent is too large to download raw Lidar data.  Please zoom in more and draw a new box.");
    			return;
    		}
    		
    		var packageTrue = sdeLayer.indexOf("Package");
    		
    		if (zoomlevel <=2 && packageTrue == -1){
    			alert("This extent is too large to download data packages.  Please zoom in more and and draw a new box.");
    			return;
    		}
    				
    		if (test != false) {
    			var opt = {
    				method: "POST"
    			};
    			
    			request(requestURL, opt).then(function(data){
    			    // data hander goes here
    			}, function(e){
    			    // error handler goes here
    				console.log('The request has failed. Error object is below.');
    				console.log(e);
    			}, function(evt){
    			    // progress event handler goes here
    				console.log('Progress event object below.');
    				console.log(evt);
    			});
    			
    			alert("Your data request has been sent to the City of Surrey's Data Download Server Queue.  A download link to your requested data will be emailed to you shortly (5-60 minutes).");
    		} 
    		else {
    			return;
    		}
    	}
    	
    	function echeck(str) {
    
    		var at = "@";
    		var dot = ".";
    		var lat = str.indexOf(at);
    		var lstr = str.length;
    		
    		if (str.indexOf(at) == -1) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.indexOf(at) == -1 || str.indexOf(at) == 0 || str.indexOf(at) == lstr) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.indexOf(dot) == -1 || str.indexOf(dot) == 0 || str.indexOf(dot) == lstr) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.indexOf(at, (lat + 1)) != -1) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.substring(lat - 1, lat) == dot || str.substring(lat + 1, lat + 2) == dot) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.indexOf(dot, (lat + 2)) == -1) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		if (str.indexOf(" ") != -1) {
    			alert("Invalid E-mail ID");
    			return false;
    		}
    
    		return true;
    	}
    });
    
    $("#map").css("width", "95%");
});