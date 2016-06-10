/* Paraphrase Clustering Interface
 * ppclust.js
 * Javascript and JQuery functions
 * Last edited: 18 Jun 2015 by Anne Cocos, previously by Alex Harelick
 */

var numOfRows = 1;
var numOfCols = 1;

var sortNew = false;
var starter;
var crowdstarter;
var ppArray;
var unsortedlist;

var mergedBins = [];
var mergestage = true;

function check() {
		var empty = false;
		$( "ul.sortbin" ).each(function(index) {
		  	if (($(this).children().length) == 0) {
		  		empty = true;
		  	}
		});
		if (!empty) {
			numOfCols = (numOfCols % 3) + 1;
			if (numOfCols % 3 == 1) {
				numOfRows++;
		  		$('.last').removeClass("last").after('<div id=\"row' + numOfRows + '\" class=\"row last\"><div class=\"col-sm-offset-0 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div></div>');
			} else {
				$('.last>div:last-child').after('<div class=\"col-sm-offset-1 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div>');
			}
		  	readyBoxes();
		}
	}

var validate = false;
var duplicated = false;

function initClasses(classstr) {
	numOfRows = 1;
	numOfCols = 1;
	$('#sortarea').html('<div id="row1" class="row last"><div class="col-sm-offset-0 col-sm-3"><ul class="sortbin draggable"></ul></div></div><div class="trashbin"><ul class="trash draggable part2"></ul></div>');
	console.log(classstr);
	$.each(classstr, function(classid, wordset) {
		var classmembers = wordset;
		numOfCols = (numOfCols % 3) + 1;
		if (numOfCols % 3 == 1) {
			numOfRows++;
			var wordlist = '';
		  	$.each(classmembers, function(intValue, word) {
		  		wordlist += '<li class="ui-priority-secondary goldtopic"><span class="topicWords">' + word + '</span></li>';
		  	});
		  	$('.last>div:last-child ul.sortbin').addClass("gold");
		  	if (classid.indexOf('gold') >= 0) {  // merged
		  		$('.last>div:last-child ul.sortbin').attr("id", classid);
		  	} else {  // initial
		  		$('.last>div:last-child ul.sortbin').attr("id", 'goldclass'+classid.toString());
		  	}
		  	$('.last>div:last-child ul.sortbin').append(wordlist);
		  	$('.last').removeClass("last").after('<div id=\"row' + numOfRows + '\" class=\"row last\"><div class=\"col-sm-offset-0 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div></div>');
		} else {
			var wordlist = '';
		  	$.each(classmembers, function(intValue, word) {
		  		wordlist += '<li class="ui-priority-secondary goldtopic"><span class="topicWords">' + word + '</span></li>';
		  	});
		  	$('.last>div:last-child ul.sortbin').addClass("gold");
		  	if (classid.indexOf('gold') >= 0) { // merged
		  		$('.last>div:last-child ul.sortbin').attr("id", classid);
		  	} else {  // initial
		  		$('.last>div:last-child ul.sortbin').attr("id", 'goldclass'+classid.toString());
		  	}
		  	$('.last>div:last-child ul.sortbin').append(wordlist)
			$('.last>div:last-child').after('<div class=\"col-sm-offset-1 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div>');
		}

	});
}

function readyBoxes() {
	$(".sortbin")
		.sortable({
			connectWith: "ul",
			revert: '150',
			receive: check
		})
		.droppable()  
		.draggable( {
			containment: "#sortarea"
		})
	$(".sortbin").click(function() {
		if (sortNew == true) {
			$(this).toggleClass('sel');
		}
	});
	$(".trash")
		.sortable({
			connectWith: "ul",
			revert: '150',
			receive: check
		})
		.droppable()
	$("#topic-box")
		.sortable({
			connectWith: "ul",
			revert: '150',
		})
		.droppable()
	$(".goldtopic")
		.draggable( {
			containment: "parent"
		})
}

function showHideExample() {
    $(".flip").click(function() {
		$(".togglepanel").toggle();
	});
}

function duplicate() {
	$(".dup").click(function(intVar, word) {
		var dupword = this.id.replace("_","");
		if (!duplicated) {
			$("#dupWord").append(dupword);
			$("#dialog_dup").dialog();
			duplicated = true;
		}
		$('#topic-box').append('<li class="ui-state-default topics"><span class="topicWords">' + dupword + '</span></li>');
	});
}

function validateForm() {
	$('#submitButton').click(function () {
		if (validate) {
			return true;
		} else {
			alert('Please sort all words and click the green button before pressing Submit.');
			return false;
		}
	});
}

function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex ;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function readyOutput() {
	$('#done').click(function() {
		if ($('#topic-box').children().length != 0) {
			$(this).removeClass("btn-success").addClass("btn-danger");
			$(this).html("You Have to Sort All Words");
			setTimeout(function() {
				$('#done').removeClass("btn-danger").addClass("btn-success");
				$('#done').html("Click Here When Complete");
			}, 3000);
			validate = false;
		} else {
			var boxNum = 1;
			$( "ul" ).each(function(index, bin) {
				var answers;
				if (($(bin).children().length) != 0 && $(bin).hasClass('sortbin')) {
					answers = "";
					$(bin).children('li').each(function(index, child) {
						answers += ($(child).children('span').html() + '@!');
					});
					$('input[name=box' + boxNum + ']').remove();
					if ($(bin).hasClass('gold')) {
						$('#output').append('<input name="' + $(bin).attr('id') + '" value="' + answers + '" style="display:none;"></input>');
					} else {
						$('#output').append('<input name="newbox' + boxNum + '" value="' + answers + '" style="display:none;"></input>');
						boxNum++;
					}
				} else if ($(bin).hasClass('trash')) {
					answers = "";
					$(bin).children('li').each(function(index, child) {
						answers += ($(child).children('span').html() + '@!');
					});
					$('input[name=trash]').remove();
					$('#output').append('<input name="trash" value="' + answers + '" style="display:none;"></input>');
				}	
			});
			for (var i=0, c=mergedBins.length; i < c; i++) {
				$('#output').append('<input name="merged' + i.toString() + '" value="' + mergedBins[i] + '" style="display:none;"></input>');
			}

			var unsortedstr = '<input name="unsorted" value="[';
			var j;
			for (j=0; j<unsortedlist.length - 1; j++) {
				unsortedstr = unsortedstr + unsortedlist[j] + ', ';
			}
			unsortedstr = unsortedstr + unsortedlist[unsortedlist.length-1] + ']" style = "display:none;">';
			$('#output').append(unsortedstr);

			$(this).html("Thanks, now you can submit the HIT");
			validate = true;		
		}
		console.log($('#output').html());
	});

}
function readyButtons() {
	$('#move2').click(function() {
		$('.part1').hide();
		$('.part2').show();
		sortNew = false;
		$('.sel').toggleClass('sel');
	});
	$('#move1').click(function() {
		$('.part2').hide();
		$('.part1').show();		
		sortNew = true;
	});
	$('#reset').click(function() {
		if (confirm('Are you sure you want to start over?')) {
			init();
		}
	});
	$('#merge').click(function() {
		var mergedWords = [];
		var binNames = [];
		var unmerged = {};
		
		var mergedcount = 0;  // validation for Merge button
		$( "ul" ).each(function(index, bin) {
			if ($(bin).children().length > 0 && $(bin).hasClass('sel')) {
				mergedcount ++;
			}
			if ($(bin).hasClass('gold') && $(bin).hasClass('sel')) {
				binNames = binNames.concat([$(bin).attr('id')]);
			}
		});
		if (mergedcount <2) {  // validation
			$("#dialog_mergeval").dialog();
		}
		else {
			$( "ul" ).each(function(index, bin) {  // TODO: Name bins appropriately and handle names in initClasses       
				if ($(bin).children().length > 0 && $(bin).hasClass('sel')) {
					$(bin).children('li').each(function(index, child) {
						mergedWords = mergedWords.concat([$(child).children('span').html()]);
					});
				} else if ($(bin).children().length > 0 && $(bin).hasClass('sortbin')) {
					var words = [];
					$(bin).children('li').each(function(index, child) {
						words = words.concat([$(child).children('span').html()]);
					});
					unmerged[$(bin).attr('id')] = words;
				}
			});
			unmerged[binNames[0]] = mergedWords;
			initClasses(unmerged);
			readyBoxes();
			$('.part2').hide();
			$('.part1').show();
			
			if (binNames.length > 1) {
				mergedBins = mergedBins.concat([binNames]);
			}
			console.log(mergedBins);
		}
	});
}

function init() {

	$('#topic-box').html('');
	$('.dropdown-menu').html('');
	for (i in ppArray) {
		$('#topic-box').append('<li class="ui-state-default topics"><span class="topicWords">' + ppArray[i] + '</span></li>');
		$('.dropdown-menu').append('<li><a href="#" class="dup" id="_' + ppArray[i] + '">' + ppArray[i] + '</a></li>');
	}
	
	starter = '{"1": ["about", "approximately", "some"], "0": ["about"], "2": ["round"]}';
	crowdstarter = $.parseJSON(starter);
	//var crowdstarter = ${crowdstarter};

	var crowdlength = 0;
	var i;
	for (i in crowdstarter) {
		if (crowdstarter.hasOwnProperty(i)) {
			crowdlength ++;
		}
	}
	
	if (crowdlength > 0 && mergestage == true) {
		sortNew = true;
	} else {
		sortNew = false;
	}
	
	$('.dropdown-toggle').dropdown()
	
	initClasses(crowdstarter);
	readyBoxes();

	if (sortNew == true) {
		$('.part2').hide();
		$('.part1').show();
	} else {
		$('.part1').hide();
		$('.part2').show();
		$('.onlyShowWithSortStage').hide();
	}

	showHideExample();
	duplicate();
	validateForm();
	readyOutput();
}

$(document).ready(function() {
	//var unsortedlist = ${unsorted};
	unsortedlist = ['approx', 'almost', 'over', 'all', 'ap', 'as', 'sometime', 'through', 'in', 'close'];
	ppArray = unsortedlist.concat(['${bogus}']);
	
    var i;
    for (i=0; i<unsortedlist.length; i++) {
        unsortedlist[i] = decodeURIComponent(escape(unsortedlist[i]));
	}
	
	shuffle(ppArray);
	console.log(ppArray);
	readyButtons();

	init();
});

	