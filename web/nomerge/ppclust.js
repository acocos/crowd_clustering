/* Paraphrase Clustering Interface
 * ppclust.js
 * Javascript and JQuery functions
 * Last edited: 18 Jun 2015 by Anne Cocos
 */

var numOfRows = 1;
var numOfCols = 1;

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
	console.log(classstr);
	$.each(classstr, function(classnum, wordset) {
		var classmembers = wordset;
		numOfCols = (numOfCols % 3) + 1;
		if (numOfCols % 3 == 1) {
			numOfRows++;
			var wordlist = '';
		  	$.each(classmembers, function(intValue, word) {
		  		wordlist += '<li class="ui-priority-secondary goldtopic"><span class="topicWords">' + word + '</span></li>';
		  	});
		  	$('.last>div:last-child ul.sortbin').addClass("gold");
		  	$('.last>div:last-child ul.sortbin').attr("id", 'goldclass'+classnum.toString());
		  	$('.last>div:last-child ul.sortbin').append(wordlist);
		  	$('.last').removeClass("last").after('<div id=\"row' + numOfRows + '\" class=\"row last\"><div class=\"col-sm-offset-0 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div></div>');
		} else {
			var wordlist = '';
		  	$.each(classmembers, function(intValue, word) {
		  		wordlist += '<li class="ui-priority-secondary goldtopic"><span class="topicWords">' + word + '</span></li>';
		  	});
		  	$('.last>div:last-child ul.sortbin').addClass("gold");
		  	$('.last>div:last-child ul.sortbin').attr("id", 'goldclass'+classnum.toString());
		  	$('.last>div:last-child ul.sortbin').append(wordlist)
			$('.last>div:last-child').after('<div class=\"col-sm-offset-1 col-sm-3\"><ul class=\"droptrue sortbin\"></ul></div>');
		}
		//$('.goldtopic').draggable('disable');
		readyBoxes();

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
		if (!duplicated) {
			$("#dupWord").append(this.id);
			$("#dialog").dialog();
			duplicated = true;
		}
		$('#topic-box').append('<li class="ui-state-default topics"><span class="topicWords">' + this.id + '</span></li>');
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
			$(this).html("Thanks, now you can submit the HIT");
			validate = true;		
		}
		console.log($('#output').html());
	});

}
$(document).ready(function() {

	//var unsortedlist = ${unsorted};
	var unsortedlist = ['approx', 'almost', 'over']; //, 'all', 'ap', 'as', 'sometime', 'through', 'in', 'close'];
	var ppArray = unsortedlist.concat(['${bogus}']);
	
	shuffle(ppArray);
	console.log(ppArray);

	for (i in ppArray) {
		$('#topic-box').append('<li class="ui-state-default topics"><span class="topicWords">' + ppArray[i] + '</span></li>');
		$('.dropdown-menu').append('<li><a href="#" class="dup" id="' + ppArray[i] + '">' + ppArray[i] + '</a></li>');
	}
	

	//var nclasses = ${num_classes};
	var nclasses = 3;
	//var starter = '{"1": ["about", "approximately", "some"], "0": ["about"], "2": ["round"]}';
	var starter = '{}';
	var crowdstarter = $.parseJSON(starter);
	
	//var crowdstarter = ${crowdstarter};

		
	$('.dropdown-toggle').dropdown()
	
	initClasses(crowdstarter);
	readyBoxes();
	showHideExample();
	duplicate();
	validateForm();
	readyOutput();
});

	